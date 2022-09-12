from django.dispatch import receiver

from apps.shop.models import Order
from apps.shop.signals import order_paid
from .models import KomtetRequest


@receiver(order_paid, sender=Order)
def komtet_request(sender, instance, **kwargs):
    """Отправка информации о заказе в комтет-кассу"""
    KomtetRequest.register_order(instance)
