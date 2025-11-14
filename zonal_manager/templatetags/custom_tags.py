from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr_name):
    """Safely get an attribute by name in a Django template."""
    return getattr(obj, attr_name, '')
