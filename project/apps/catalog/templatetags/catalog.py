from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def convert_price(price):
    price = str(intcomma(int(price or 0))).replace(',', ' ')
    return f'{price} ₽'


def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False

@register.filter
def get_minmax(period: str, minmax: str):
    period = str(period)
    if '-' in period:
        v_min, v_max = period.split('-')

        result = None

        if(minmax == "min" and is_float(v_min)):
            result = int(float(v_min))
        elif(minmax == "max" and is_float(v_max)):
            result = int(float(v_max))

        return result

        #if(str.isdigit(v_min) and str.isdigit(v_max)):
        #    return int(float(v_min)) if minmax == 'min' else int(float(v_max))


@register.filter
def contain(array, obj):
    if not array:
        array = []
    return str(obj) in list(map(str, array))


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def get(dictionary, value):
    return dictionary.get(value)


def _get_function(obj, func_name, *args, **kwargs):
    if hasattr(obj, func_name):
        return getattr(obj, func_name)(*args, **kwargs)


@register.filter
def get_name(obj):
    return obj._meta.app_label


@register.filter
def get_model(obj):
    return obj._meta.object_name

@register.filter
def get_calc_price(line, height):
    items, price = line.calc(height)
    return {
        'items': items,
        'price': price,
    }



@register.simple_tag(takes_context=True)
def isPaginationPage(context):
    request = context.request
    return bool(request.GET.get("page", False))