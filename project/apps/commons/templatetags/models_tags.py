from django import template
register = template.Library()


@register.filter
def verbose_name(obj):
    return obj.__dict__


@register.filter
def verbose_name_plural(obj):
    return obj._meta.verbose_name_plural
