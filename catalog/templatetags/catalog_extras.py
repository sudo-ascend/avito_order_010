from __future__ import annotations

from django import template
from django.templatetags.static import static

register = template.Library()


@register.filter
def asset_url(value):
    if not value:
        return ""
    path = str(value)
    if path.startswith(("http://", "https://", "/")):
        return path
    return static(path)


@register.filter
def times(number):
    try:
        value = int(number)
    except (TypeError, ValueError):
        return range(0)
    return range(max(value, 0))
