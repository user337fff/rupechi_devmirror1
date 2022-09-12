from django.core.cache import cache
from django.template import Library
from django.template.loader import render_to_string

register = Library()

@register.simple_tag(takes_context=True)
def get_top_header_items(context):
    result = cache.get("top_header_items", False)
    if(not result):
        print("Не используем кэш")
        result = render_to_string(
            "nav/top_header_items.html", 
            {
                "header_items": context["header_items"]
            }
        )
        cache.set("top_header_items", result)
    else:
        print("Используем кэш")
    return result

@register.simple_tag(takes_context=True)
def get_top_catalog_items(context):
    result = cache.get("top_catalog_items", False)
    if(not result):
        print("Не используем кэш")
        result = render_to_string(
            "nav/top_catalog_items.html",
            {
                "catalog_items": context["catalog_items"]
            }
        ) 
        cache.set("top_catalog_items", result)
    else:
        print("Используем кэш")
    return result

@register.simple_tag(takes_context=True)
def get_middle_catalog_items(context):
    result = cache.get("middle_catalog_items", False)
    if(not result):
        print("Не используем кэш")
        result = render_to_string(
            "nav/middle_catalog_items.html",
            {
                "catalog_items": context["catalog_items"]
            }
        )
        cache.set("middle_catalog_items", result)
    else:
        print("Используем кэш")
    return result

@register.simple_tag(takes_context=True)
def get_footer_items(context):
    result = cache.get("footer_items", False)
    if(not result):
        print("Не используем кэш")
        result = render_to_string(
            "nav/footer_items.html",
            {
                "footer_items": context["footer_items"]
            }
        )
        cache.set("footer_items", result)
    else:
        print("Используем кэш")
    return result

@register.simple_tag(takes_context=True)
def get_bottom_header_items(context):
    result = cache.get("bottom_header_items", False)
    if(not result):
        print("Не используем кэш")
        result = render_to_string(
            "nav/bottom_header_items.html",
            {
                "header_items": context["header_items"]
            }
        )
        cache.set("bottom_header_items", result)
    else:
        print("Используем кэш")
    return result

@register.simple_tag(takes_context=True)
def get_bottom_catalog_items(context):
    result = cache.get("bottom_catalog_items", False)
    if(not result):
        print("Не используем кэш")
        result = render_to_string(
            "nav/bottom_catalog_items.html",
            {
                "catalog_items": context["catalog_items"]
            }
        )
        cache.set("bottom_catalog_items", result)
    else:
        print("Используем кэш")
    return result