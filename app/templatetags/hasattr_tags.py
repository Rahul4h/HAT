# app/templatetags/hasattr_tags.py

from django import template
import builtins

register = template.Library()

@register.filter
def hasrel(obj, attr_name):
    """Check if object has attribute without causing recursion."""
    return builtins.hasattr(obj, attr_name)
