import django.dispatch


"""Кастомные сигналы для заказа"""

# данный сигнал использует бонусная система
order_created = django.dispatch.Signal(providing_args=["order"])
order_paid = django.dispatch.Signal(providing_args=["order"])
