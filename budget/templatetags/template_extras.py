from django import template
register = template.Library()

@register.filter
def get_item(obj, attr):
    """Return obj[attr] for dicts or getattr(obj, attr) for objects."""
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)
