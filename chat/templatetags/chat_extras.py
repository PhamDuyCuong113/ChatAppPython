from django import template
import os

register = template.Library()

@register.filter
def endswith(value, arg):
    """Trả về True nếu chuỗi value kết thúc bằng arg (không phân biệt hoa/thường)."""
    if not value:
        return False
    try:
        return str(value).lower().endswith(str(arg).lower())
    except Exception:
        return False


@register.filter
def basename(value):
    """Trả về tên file (không bao gồm đường dẫn)."""
    try:
        # Nếu là FileField, lấy thuộc tính name hoặc url
        if hasattr(value, "name") and value.name:
            value = value.name
        elif hasattr(value, "url") and value.url:
            value = value.url
        return os.path.basename(str(value))
    except Exception:
        return value


@register.filter
def username_to_hue(username):
    """Tạo giá trị Hue (0–360) ổn định dựa theo username."""
    if not username:
        return 200
    return abs(hash(username)) % 360


@register.filter
def split_first(value, arg=" "):
    """Lấy phần đầu tiên của chuỗi sau khi tách bằng ký tự arg."""
    if not value:
        return ""
    try:
        return str(value).split(str(arg))[0].strip()
    except Exception:
        return value
