from django.apps import AppConfig


class CartConfig(AppConfig):
    name = 'apps.cart'
    verbose_name = 'Корзина'

    def ready(self):
        import apps.cart.signals
