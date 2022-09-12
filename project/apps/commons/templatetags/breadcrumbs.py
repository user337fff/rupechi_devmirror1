from django import template

register = template.Library()


@register.inclusion_tag('commons/breadcrumbs.html')
def breadcrumbs(obj):
    return {'breadcrumbs': obj.get_breadcrumbs()}
