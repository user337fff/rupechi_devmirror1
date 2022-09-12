from django.db.models import signals
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.shop.models import Order
from apps.shop.signals import order_created
from .models import BonusAccount, Action

User = get_user_model()


@receiver(signals.post_save, sender=User)
def bonuses_for_register(sender, instance, created, **kwargs):
    """Начисление бонусов за регистрацию"""
    if created:
        asof = timezone.now()
        account, action = BonusAccount.create(user=instance, asof=asof)
        account.deposit_register_bonuses()


@receiver(signals.post_save, sender=Order)
def deposit_for_completed_order(sender, instance, created, **kwargs):
    """Начисление бонусов заказа"""
    if instance.user:
        instance.user.bonus_account.deposit_for_completed_order(instance)


@receiver(order_created, sender=Order)
def withdraw_from_order(sender, instance, **kwargs):
    """Списание бонусов заказа"""
    if instance.user:
        instance.user.bonus_account.withdraw_from_order(instance)
