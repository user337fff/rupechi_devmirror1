import traceback
from .cart import Cart, CartItem
from .unauth_cart import UnauthCart
from apps.catalog.models import Brand, Category


def get_gefest(cart):
    try:
        print("----------Check gefest--------------")
        gefest_id_1c = '7b727b97-268e-11ea-a755-ff02e87939d1'
        gefest = Brand.objects.get(id_1c=gefest_id_1c)
        gefest_items = cart.items()
        for item in gefest_items:
            print(item.product, item.product.brand)
            if item.product.brand == gefest:
                print("It's gefest!")
                return True
        return False
    except:
        traceback.print_exc()
        return False


def get_cooking_on_fire(cart):
    try:
        cooking_on_fire_categories = Category.objects.get(id_1c="361286dc-4421-11e6-bef4-aa13f697773b").get_descendants(include_self=True)
        cart_items = cart.items()
        for item in cart_items:
            print("ITEMS")
            print(item.product, item.product.category)
            if cooking_on_fire_categories.filter(pk=item.product.category.pk).exists():
                return True
        return False
    except:
        traceback.print_exc()
        return False

def get_cart(request):
    resultCart = None

    if request.user.is_authenticated:
        resultCart =  Cart.objects.get(user=request.user)
    else:
        resultCart = UnauthCart(request)

    for item in resultCart.items():
        if(item.price == 0):
            if request.user.is_authenticated:
                resultCart.remove(id=item.id)
            else:
                resultCart.remove(item.product, request.domain)
                
    return resultCart
