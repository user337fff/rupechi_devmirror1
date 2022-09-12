from apps.catalog.models import InStockNotification
from apps.feedback.mailer import Mailer

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.db import transaction


@transaction.atomic
def send_notification(item):
    html = render_to_string(
        template_name='feedback/in_stock_user/user_message.html',
        context={
            'domain': item.domain,
            'product': item.product
        }
    )

    Mailer.send(
        to=[item.user_email],
        html=html,
        subject=render_to_string(
            template_name='feedback/in_stock_user/subject.txt',
        )
    )


def check_stock():
    for item in InStockNotification.objects.all():
        print("----------------------------------------")
        print(item.product)
        print("Кол-во товара сейчас:", item.in_stock())
        print("Кол-во товара в прошлом:", item.product.lastStockQuantityBoolean)

        if item.in_stock() and item.product.lastStockQuantityBoolean == False:
            print("Высылаем сообщение")
            send_notification(item)

        item.product.lastStockQuantityBoolean = item.in_stock()

        item.product.save()