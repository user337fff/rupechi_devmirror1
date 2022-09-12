from .models import get_wishlist


def wishlist(request):
    wishlist = get_wishlist(request)
    return {'wishlist': wishlist}
