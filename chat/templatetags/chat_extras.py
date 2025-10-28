from django import template
import os
register = template.Library()

@register.filter
def endswith(value, arg):
    """Trả về True nếu chuỗi value kết thúc bằng arg"""
    if not value:
        return False
    try:
        return str(value).lower().endswith(str(arg).lower())
    except Exception:
        return False


@register.filter
def basename(value):
    """Trả về tên file (không bao gồm đường dẫn)"""
    try:
        return os.path.basename(value)
    except Exception:
        return value
