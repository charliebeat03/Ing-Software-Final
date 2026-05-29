# utils/date_utils.py - Utilidades para manejo de fechas
from datetime import datetime, date, timedelta

def get_current_date():
    """Retorna la fecha actual en formato YYYY-MM-DD"""
    return date.today().isoformat()

def get_current_datetime():
    """Retorna la fecha y hora actual"""
    return datetime.now()

def format_date(date_obj, format_str="%d/%m/%Y"):
    """Formatea una fecha a string"""
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj)
    return date_obj.strftime(format_str)

def parse_date(date_str, format_str="%d/%m/%Y"):
    """Convierte un string a fecha"""
    return datetime.strptime(date_str, format_str).date()

def get_date_range(days=7):
    """Retorna un rango de fechas de los últimos N días"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    return start_date, end_date

def is_same_day(date1, date2):
    """Verifica si dos fechas son el mismo día"""
    if isinstance(date1, str):
        date1 = datetime.fromisoformat(date1).date()
    if isinstance(date2, str):
        date2 = datetime.fromisoformat(date2).date()
    return date1 == date2