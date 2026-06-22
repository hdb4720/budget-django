from django import template
register = template.Library()

@register.filter
def get_item(obj, attr):
    if isinstance(obj, dict):
        return obj.get(attr)
    return getattr(obj, attr, None)

