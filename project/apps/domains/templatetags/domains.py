from django import template

from ..shortcuts import replace_city

register = template.Library()


@register.simple_tag(takes_context=True)
def format_city(context, value):
    try:
        domain = context['request'].domain
    except KeyError:
        return value

    return replace_city(value, domain)
