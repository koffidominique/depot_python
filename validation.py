from money import fcfa
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Optional, Union
import re

def validate_positive_number(value: Union[int, float, Decimal], field_name: str = "Value") -> Decimal:
    try:
        decimal_value = Decimal(str(value))
        if decimal_value < Decimal('0'):
            raise ValueError(f"{field_name} must be positive")
        return decimal_value
    except (InvalidOperation, TypeError):
        raise ValueError(f"{field_name} must be a valid number")

def validate_positive_integer(value: int, field_name: str = "Value") -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return value

def validate_quantity(value: Union[int, float, Decimal], field_name: str = "Quantity") -> Decimal:
    try:
        decimal_value = Decimal(str(value))
        if decimal_value <= Decimal('0'):
            raise ValueError(f"{field_name} must be greater than 0")
        return decimal_value
    except (InvalidOperation, TypeError):
        raise ValueError(f"{field_name} must be a valid quantity")

def validate_price(value: Union[int, float, Decimal], field_name: str = "Price") -> int:
    result = fcfa(value, field_name)
    if result < 0:
        raise ValueError(f"{field_name} must be positive")
    return result


def validate_amount(value: Union[int, float, Decimal], field_name: str = "Amount") -> int:
    return validate_price(value, field_name)


def validate_discount(value: Union[int, float, Decimal], field_name: str = "Discount") -> int:
    return validate_price(value, field_name)

def validate_date(value: Optional[Union[datetime, str]], field_name: str = "Date") -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise ValueError(f"{field_name} must be a valid date")
    raise ValueError(f"{field_name} must be a valid date")

def validate_reference(value: str, field_name: str = "Reference") -> str:
    if not value or not isinstance(value, str):
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > 50:
        raise ValueError(f"{field_name} is too long (max 50 characters)")
    return value.strip()

def validate_barcode(value: Optional[str], field_name: str = "Barcode") -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if len(value) > 50:
        raise ValueError(f"{field_name} is too long (max 50 characters)")
    return value

def validate_phone(value: Optional[str], field_name: str = "Phone") -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    phone_pattern = r'^\+?[\d\s-]{8,}$'
    if not re.match(phone_pattern, value):
        raise ValueError(f"{field_name} has an invalid format")
    return value

def validate_email(value: Optional[str], field_name: str = "Email") -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if not value:
        return None
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValueError(f"{field_name} has an invalid format")
    return value

def validate_string_length(value: Optional[str], max_length: int, field_name: str = "Field") -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    value = value.strip()
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long (max {max_length} characters)")
    return value

def validate_notes(value: Optional[str], field_name: str = "Notes") -> Optional[str]:
    return validate_string_length(value, 1000, field_name)

def calculate_line_total(quantity: Decimal, unit_price: Decimal, discount: Decimal = Decimal('0')) -> Decimal:
    quantity = validate_quantity(quantity)
    unit_price = validate_price(unit_price)
    discount = validate_discount(discount)
    total = quantity * unit_price - discount
    return fcfa(total, "Total de ligne")

def calculate_sale_totals(sale_lines: list) -> dict:
    total_amount = sum(line.line_total for line in sale_lines)
    discount_amount = sum(getattr(line, 'discount', Decimal('0')) for line in sale_lines)
    net_amount = total_amount - discount_amount
    return {
        'total_amount': fcfa(total_amount),
        'discount_amount': fcfa(discount_amount),
        'net_amount': fcfa(net_amount)
    }