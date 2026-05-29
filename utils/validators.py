# utils/validators.py - Validaciones de datos
import re

def validate_required(value, field_name):
    """Valida que un campo no esté vacío"""
    if not value or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"El campo '{field_name}' es requerido")
    return value

def validate_number(value, field_name, min_value=None, max_value=None):
    """Valida que un valor sea numérico y esté en rango"""
    try:
        num = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"El campo '{field_name}' debe ser un número")
    
    if min_value is not None and num < min_value:
        raise ValueError(f"El campo '{field_name}' debe ser mayor o igual a {min_value}")
    
    if max_value is not None and num > max_value:
        raise ValueError(f"El campo '{field_name}' debe ser menor o igual a {max_value}")
    
    return num

def validate_positive(value, field_name):
    """Valida que un número sea positivo"""
    return validate_number(value, field_name, min_value=0)

def validate_name(name, field_name="nombre"):
    """Valida que un nombre sea válido"""
    name = validate_required(name, field_name)
    
    # Verificar longitud
    if len(name) < 2:
        raise ValueError(f"El {field_name} debe tener al menos 2 caracteres")
    
    if len(name) > 100:
        raise ValueError(f"El {field_name} no puede exceder los 100 caracteres")
    
    # Verificar caracteres válidos
    if not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\.]+$', name):
        raise ValueError(f"El {field_name} contiene caracteres no válidos")
    
    return name.strip()

def validate_price(price):
    """Valida que un precio sea válido"""
    price = validate_positive(price, "precio")
    
    if price > 10000:  # Precio máximo razonable
        raise ValueError("El precio no puede exceder $10,000")
    
    return round(price, 2)