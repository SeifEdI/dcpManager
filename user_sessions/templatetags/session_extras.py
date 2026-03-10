from django import template
from datetime import timedelta
import math

register = template.Library()

@register.filter
def format_duration(duration):
    """
    Format a timedelta object into a human-readable string.
    """
    if not isinstance(duration, timedelta):
        return str(duration)
    
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return "Just now"
    
    minutes = total_seconds // 60
    hours = minutes // 60
    days = hours // 24
    
    if days > 0:
        remaining_hours = hours % 24
        if remaining_hours > 0:
            return f"{days} day{'s' if days != 1 else ''} {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"
        else:
            return f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        remaining_minutes = minutes % 60
        if remaining_minutes > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"

@register.filter
def format_bytes(bytes_value):
    """
    Format bytes into human-readable format.
    """
    if not bytes_value:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    return f"{s} {size_names[i]}"

@register.filter
def device_icon(device_type):
    """
    Return appropriate icon for device type.
    """
    icons = {
        'mobile': '📱',
        'tablet': '📱', 
        'desktop': '💻',
        'unknown': '🖥️'
    }
    return icons.get(device_type, '🖥️')
