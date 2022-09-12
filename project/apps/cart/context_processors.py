from .models import get_cart


def cart(request):
    """
    Добавление в контекст корзины товаров.
    """
    data = {
        'cart': get_cart(request)
    }
    return data
