from __future__ import annotations

import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from config import BACKUP_DIR, DB_PATH
from app_core.security import hash_password


SELECT_PREFIXES = ("SELECT", "PRAGMA", "WITH", "EXPLAIN")


class Database:
    _instance: "Database | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "Database":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self.db_path = Path(DB_PATH)
        self.backup_dir = Path(BACKUP_DIR)
        self._cache_lock = threading.RLock()
        self._query_cache: dict[tuple[str, tuple[Any, ...]], tuple[datetime, list[sqlite3.Row]]] = {}
        self._global_cache: dict[str, tuple[datetime, Any]] = {}

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self._configure_database()
        self._initialized = True

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA temp_store = MEMORY")
        return connection

    @contextmanager
    def connection(self) -> Iterable[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _configure_database(self) -> None:
        self._create_tables()
        self._migrate_schema()
        self._seed_defaults()
        self.create_daily_backup()
        self._cleanup_old_backups()

    def _create_tables(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS unidades_medida (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL,
            abreviatura TEXT,
            activo INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            unidad_medida_id INTEGER NOT NULL,
            stock_minimo REAL NOT NULL DEFAULT 0,
            costo_promedio REAL NOT NULL DEFAULT 0,
            fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ultima_actualizacion TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            notas TEXT,
            FOREIGN KEY (unidad_medida_id) REFERENCES unidades_medida(id)
        );

        CREATE TABLE IF NOT EXISTS inventario_ingredientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingrediente_id INTEGER NOT NULL UNIQUE,
            cantidad_actual REAL NOT NULL DEFAULT 0,
            fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
        );

        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            precio_venta REAL NOT NULL,
            unidad_venta TEXT NOT NULL,
            costo_estimado REAL NOT NULL DEFAULT 0,
            fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ultima_actualizacion TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            descripcion TEXT
        );

        CREATE TABLE IF NOT EXISTS inventario_productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL UNIQUE,
            cantidad_disponible REAL NOT NULL DEFAULT 0,
            fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL DEFAULT (DATE('now')),
            fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ingrediente_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            costo_unitario REAL NOT NULL,
            notas TEXT,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
        );

        CREATE TABLE IF NOT EXISTS pedidos_chef (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            ingrediente_id INTEGER NOT NULL,
            cantidad_total REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
        );

        CREATE TABLE IF NOT EXISTS pedidos_chef_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            hora TEXT NOT NULL DEFAULT (TIME('now')),
            cantidad REAL NOT NULL,
            motivo TEXT,
            FOREIGN KEY (pedido_id) REFERENCES pedidos_chef(id)
        );

        CREATE TABLE IF NOT EXISTS produccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            costo_total REAL DEFAULT 0,
            notas TEXT,
            hora TEXT NOT NULL DEFAULT (TIME('now')),
            fecha_registro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            fecha_hora TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            producto_id INTEGER NOT NULL,
            cantidad_total REAL NOT NULL DEFAULT 0,
            total_ventas REAL NOT NULL DEFAULT 0,
            precio_unitario REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS ventas_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER,
            hora TEXT NOT NULL DEFAULT (TIME('now')),
            cantidad REAL NOT NULL,
            precio_unitario REAL DEFAULT 0,
            subtotal REAL DEFAULT 0,
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        );

        CREATE TABLE IF NOT EXISTS excedentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            producto_id INTEGER NOT NULL,
            producido REAL NOT NULL,
            vendido REAL NOT NULL,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS ajustes_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            tipo TEXT NOT NULL,
            elemento_id INTEGER NOT NULL,
            cantidad_anterior REAL NOT NULL,
            cantidad_nueva REAL NOT NULL,
            motivo TEXT NOT NULL,
            notas TEXT
        );

        CREATE TABLE IF NOT EXISTS cierres_diarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL UNIQUE,
            total_ventas REAL NOT NULL DEFAULT 0,
            total_produccion REAL NOT NULL DEFAULT 0,
            total_excedente REAL NOT NULL DEFAULT 0,
            total_ajustes INTEGER NOT NULL DEFAULT 0,
            cerrado_por TEXT,
            fecha_cierre TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            observaciones TEXT
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            nombre_completo TEXT NOT NULL,
            rol TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            notas TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pedidos_clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_creacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            cliente_id INTEGER,
            canal TEXT NOT NULL DEFAULT 'telefonico',
            estado TEXT NOT NULL DEFAULT 'registrado',
            total REAL NOT NULL DEFAULT 0,
            notas TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS pedido_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos_clientes(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS entregas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL UNIQUE,
            repartidor TEXT,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            hora_salida TEXT,
            hora_entrega TEXT,
            observaciones TEXT,
            FOREIGN KEY (pedido_id) REFERENCES pedidos_clientes(id)
        );

        CREATE INDEX IF NOT EXISTS idx_compras_fecha ON compras(fecha);
        CREATE INDEX IF NOT EXISTS idx_pedidos_chef_fecha ON pedidos_chef(fecha);
        CREATE INDEX IF NOT EXISTS idx_produccion_fecha ON produccion(fecha);
        CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
        CREATE INDEX IF NOT EXISTS idx_ventas_detalle_venta ON ventas_detalle(venta_id);
        CREATE INDEX IF NOT EXISTS idx_cierres_fecha ON cierres_diarios(fecha);
        """
        with self.connection() as conn:
            conn.executescript(schema)

    def _migrate_schema(self) -> None:
        expected_columns = {
            "ingredientes": {
                "ultima_actualizacion": "TEXT",
            },
            "productos": {
                "ultima_actualizacion": "TEXT",
            },
            "compras": {
                "fecha_hora": "TEXT",
            },
            "ventas": {
                "fecha_hora": "TEXT",
            },
            "ventas_detalle": {
                "producto_id": "INTEGER",
                "precio_unitario": "REAL DEFAULT 0",
                "subtotal": "REAL DEFAULT 0",
            },
        }
        with self.connection() as conn:
            for table_name, columns in expected_columns.items():
                existing = {
                    row["name"]
                    for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                }
                for column_name, sql_type in columns.items():
                    if column_name not in existing:
                        conn.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}"
                        )

            conn.execute(
                """
                UPDATE ventas
                SET fecha_hora = COALESCE(fecha_hora, fecha || ' ' || TIME('now'))
                WHERE fecha_hora IS NULL OR TRIM(fecha_hora) = ''
                """
            )
            conn.execute(
                """
                UPDATE compras
                SET fecha_hora = COALESCE(fecha_hora, fecha || ' ' || TIME('now'))
                WHERE fecha_hora IS NULL OR TRIM(fecha_hora) = ''
                """
            )
            conn.execute(
                """
                UPDATE ventas_detalle
                SET producto_id = (
                    SELECT producto_id FROM ventas WHERE ventas.id = ventas_detalle.venta_id
                )
                WHERE producto_id IS NULL
                """
            )
            conn.execute(
                """
                UPDATE ventas_detalle
                SET precio_unitario = COALESCE(
                    precio_unitario,
                    (SELECT precio_unitario FROM ventas WHERE ventas.id = ventas_detalle.venta_id),
                    0
                )
                """
            )
            conn.execute(
                """
                UPDATE ventas_detalle
                SET subtotal = COALESCE(subtotal, cantidad * precio_unitario, 0)
                """
            )

    def _seed_defaults(self) -> None:
        units = [
            ("Kilogramo", "ingrediente", "kg"),
            ("Gramo", "ingrediente", "g"),
            ("Litro", "ingrediente", "L"),
            ("Mililitro", "ingrediente", "ml"),
            ("Unidad", "general", "ud"),
            ("Paquete", "ingrediente", "paq"),
            ("Porcion", "producto", "porc"),
        ]
        default_users = [
            ("admin", "Administrador General", "administrador", "admin123"),
            ("recepcion", "Recepcion Principal", "recepcionista", "recepcion123"),
            ("chef", "Chef de Cocina", "chef", "chef123"),
            ("gerente", "Gerencia", "gerente", "gerente123"),
        ]

        with self.connection() as conn:
            for nombre, tipo, abreviatura in units:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO unidades_medida (nombre, tipo, abreviatura)
                    VALUES (?, ?, ?)
                    """,
                    (nombre, tipo, abreviatura),
                )

            for username, nombre_completo, rol, password in default_users:
                existing = conn.execute(
                    "SELECT id FROM usuarios WHERE username = ?",
                    (username,),
                ).fetchone()
                if existing:
                    continue
                salt, digest = hash_password(password)
                conn.execute(
                    """
                    INSERT INTO usuarios (username, nombre_completo, rol, password_salt, password_hash)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, nombre_completo, rol, salt, digest),
                )

    def execute_query(
        self,
        query: str,
        params: Iterable[Any] | None = None,
        *,
        commit: bool | None = None,
    ) -> list[sqlite3.Row]:
        params_tuple = tuple(params or ())
        query_type = query.lstrip().split(None, 1)[0].upper() if query.strip() else ""
        should_commit = commit if commit is not None else query_type not in SELECT_PREFIXES

        with self.connection() as conn:
            cursor = conn.execute(query, params_tuple)
            if should_commit:
                conn.commit()
            rows = cursor.fetchall() if cursor.description else []

        if should_commit:
            self.clear_query_cache()
            self.clear_global_cache()
        return rows

    def execute_cached_query(
        self,
        query: str,
        params: Iterable[Any] | None = None,
        *,
        cache_ttl: int = 60,
    ) -> list[sqlite3.Row]:
        params_tuple = tuple(params or ())
        cache_key = (query.strip(), params_tuple)
        now = datetime.now()
        with self._cache_lock:
            cached = self._query_cache.get(cache_key)
            if cached and cached[0] > now:
                return cached[1]

        rows = self.execute_query(query, params_tuple, commit=False)
        with self._cache_lock:
            self._query_cache[cache_key] = (now + timedelta(seconds=cache_ttl), rows)
        return rows

    def execute_insert(self, query: str, params: Iterable[Any] | None = None) -> int:
        params_tuple = tuple(params or ())
        with self.connection() as conn:
            cursor = conn.execute(query, params_tuple)
            last_row_id = int(cursor.lastrowid)
        self.clear_query_cache()
        self.clear_global_cache()
        return last_row_id

    def get_one(
        self,
        table: str,
        where_clause: str,
        params: Iterable[Any] | None = None,
    ) -> sqlite3.Row | None:
        query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"
        rows = self.execute_query(query, params, commit=False)
        return rows[0] if rows else None

    def get_all(
        self,
        table: str,
        where_clause: str | None = None,
        params: Iterable[Any] | None = None,
        order_by: str | None = None,
    ) -> list[sqlite3.Row]:
        query = f"SELECT * FROM {table}"
        if where_clause:
            query += f" WHERE {where_clause}"
        if order_by:
            query += f" ORDER BY {order_by}"
        return self.execute_query(query, params, commit=False)

    def update(
        self,
        table: str,
        data: dict[str, Any],
        where_clause: str,
        params: Iterable[Any] | None = None,
    ) -> None:
        assignments: list[str] = []
        values: list[Any] = []
        for key, value in data.items():
            if value == "CURRENT_TIMESTAMP":
                assignments.append(f"{key} = CURRENT_TIMESTAMP")
            else:
                assignments.append(f"{key} = ?")
                values.append(value)
        query = f"UPDATE {table} SET {', '.join(assignments)} WHERE {where_clause}"
        self.execute_query(query, [*values, *(params or ())], commit=True)

    def get_cached_data(self, key: str) -> Any | None:
        with self._cache_lock:
            cached = self._global_cache.get(key)
            if not cached:
                return None
            expires_at, value = cached
            if expires_at < datetime.now():
                self._global_cache.pop(key, None)
                return None
            return value

    def set_cached_data(self, key: str, value: Any, ttl: int = 60) -> None:
        with self._cache_lock:
            self._global_cache[key] = (datetime.now() + timedelta(seconds=ttl), value)

    def clear_query_cache(self) -> None:
        with self._cache_lock:
            self._query_cache.clear()

    def clear_global_cache(self) -> None:
        with self._cache_lock:
            self._global_cache.clear()

    def create_daily_backup(self) -> Path:
        today_suffix = datetime.now().strftime("%Y%m%d")
        backup_path = self.backup_dir / f"backup_{today_suffix}.db"
        if backup_path.exists():
            return backup_path
        if self.db_path.exists():
            shutil.copy2(self.db_path, backup_path)
        return backup_path

    def _cleanup_old_backups(self, days_to_keep: int = 30) -> None:
        threshold = datetime.now() - timedelta(days=days_to_keep)
        for backup_file in self.backup_dir.glob("backup_*.db"):
            modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if modified < threshold:
                backup_file.unlink(missing_ok=True)

    def close_all_connections(self) -> None:
        return None

    def _get_raw_connection(self) -> sqlite3.Connection:
        return self._connect()


db = Database()


def get_connection() -> sqlite3.Connection:
    return db._get_raw_connection()


def execute_query(query: str, params: Iterable[Any] | None = None) -> list[sqlite3.Row]:
    return db.execute_query(query, params, commit=False)


def execute_insert(query: str, params: Iterable[Any] | None = None) -> int:
    return db.execute_insert(query, params)


def execute_cached_query(
    query: str,
    params: Iterable[Any] | None = None,
    *,
    cache_ttl: int = 60,
) -> list[sqlite3.Row]:
    return db.execute_cached_query(query, params, cache_ttl=cache_ttl)


def get_cached_data(key: str) -> Any | None:
    return db.get_cached_data(key)


def set_cached_data(key: str, value: Any, ttl: int = 60) -> None:
    db.set_cached_data(key, value, ttl)


def clear_query_cache() -> None:
    db.clear_query_cache()


def clear_global_cache() -> None:
    db.clear_global_cache()


def _get_raw_connection() -> sqlite3.Connection:
    return db._get_raw_connection()
