import io
import os
from datetime import timedelta

import xlsxwriter

from django.db import models
from django.db.models import Sum
from django.apps import apps
from django.utils import timezone

from apps.commons.export import ExportLimiter, ExportXlsx

from .models import Account


class AccountForExport(Account):
    """
    Вспомогательная прокси-модель для извлечения информации о пользователе
    """

    def _get_orders(self):
        return self.orders.all()

    def get_orders(self):
        orders = [
            f"Заказ №{order.id} Сумма: {order.get_total()}"
            for order in self._get_orders()
        ]
        return "\n".join(orders)

    def get_total_orders(self):
        total = self.orders.aggregation(total_sum=Sum("total"))
        return total["total_sum"]

    def _get_cart_items(self):
        return self.cart.items.all().select_related("product")

    def get_cart(self):
        cart_items = self._get_cart_items()
        cart_list = [
            f"{item.product.title} Количество: {item.count}"
            for item in cart_items
        ]
        return "\n".join(cart_list)

    class Meta:
        proxy = True


class ExportLimiterAccount(ExportLimiter):
    PERIOD_REPEAT = 60 * 2

    @classmethod
    def export(cls, user):
        return super().export(user, ExportXlsxAccount().export2bytes)


class ExportXlsxAccount(ExportXlsx):
    folder = "users/xlsx/"
    file_prefix = "users"

    def __init__(self) -> None:
        if apps.app_configs.get("shop"):
            self.shop_exist = True
        else:
            self.shop_exist = False

    def get_users(self):
        return AccountForExport.objects.all()

    def _get_headline(self) -> list:
        headline = ["Имя", "Почта", "Телефон"]
        if self.shop_exist:
            headline += ["Заказы", "Сумма покупок", "Текущая корзина"]
        return headline

    def _export(self):
        worksheet = self.workbook.add_worksheet()
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 35)
        worksheet.set_column(2, 2, 20)
        # Заголовок таблицы
        headline = self._get_headline()
        for col, item in enumerate(headline):
            worksheet.write(0, col, item)
        users = self.get_users()
        print(users)
        for row, user in enumerate(users, 1):
            print(user.name, user.email)
            worksheet.write(row, 0, user.name)
            worksheet.write(row, 1, user.email)
            worksheet.write(row, 2, user.phone)
            if self.shop_exist:
                worksheet.write(row, 3, user.get_orders())
                # worksheet.write(row, 4, user.get_total_orders())
                # worksheet.write(row, 5, user.get_cart())

        self.workbook.close()
        return self.result
