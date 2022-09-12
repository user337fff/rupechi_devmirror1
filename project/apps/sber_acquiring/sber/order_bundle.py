import re
import json

from .const import PaymentMethod, PaymentObject


class OrderBundle:
    """
    Корзина заказа
        created_at - дата создания заказа
        customer - информация о покупателе
        items - товарные позиции
    """
    DATE_PATTERN = '%Y-%m-%DT%H:%M:%S'

    created_at = None
    customer = None

    def __init__(self, created_at=None, customer=None, items=None):
        # orderCreationDate
        # customerDetails
        # cartItems
        if created_at is not None:
            self.created_at = created_at
        if customer is not None:
            self.customer = customer
        if items is None:
            self.items = []
        else:
            self.items = items

    def set_customer(self,
                     phone=None,
                     email=None,
                     contact=None,
                     full_name=None,
                     passport=None,
                     inn=None):
        """
        Установка данных о покупателе
            phone - номер телефона, возможны только цифры и знак +
            email - почта
            contact - способ связи с покупателем
        """
        data = {}

        if phone is None and email is None:
            raise TypeError(
                "set_customer() missing required"
                "positional argument: phone or email"
            )

        if phone is not None:
            data['phone'] = self.clear_phone(phone)
        if email is not None:
            data['email'] = email
        if contact is not None:
            data['contact'] = contact
        if full_name is not None:
            data['fullName'] = full_name
        if passport is not None:
            data['passport'] = passport
        if inn is not None:
            if len(inn) not in [10, 12]:
                raise TypeError('inn len must be 10 or 12 symbols')
            else:
                data['inn'] = inn
        self.customer = data

    def set_delivery_info(self,
                          city,
                          post_address,
                          country='RU',
                          delivery_type=None):
        """
        Информация о доставке
            country - Двухбуквенный код страны доставки
            city - Город доставки
            postAddress - Адрес доставки
            deliveryType - способ доставки
        """

        if self.customer is None:
            raise TypeError(
                "{} missing required property: {}".format(
                    type(self).__name__, 'customer'))

        self.customer['deliveryInfo'] = {
            'country': country,
            'city': city,
            'postAddress': post_address
        }
        if delivery_type is not None:
            self.customer['deliveryInfo']['deliveryType'] = delivery_type

    @classmethod
    def clear_phone(cls, value):
        return re.sub("[^0-9]", "", value)

    def add_item(self,
                 title,
                 uid,
                 price,
                 quantity,
                 measure='штук',
                 discount_type=None,
                 discount_value=None,
                 tax_type=None,
                 tax_sum=None,
                 payment_method=PaymentMethod.FULL_PRE,
                 payment_object=PaymentObject.PRODUCT,
                 **kwagrs):
        """
        Добавление элемента корзины
            title - имя
            uid - идентификатор в системе магазина
            price - стоимость одной позиции в минимальных единицах валюты
            quantity - количество товарных позиций данного элемента
            measure - мера измерения количества
            discount_type - тип скидки на товарную позицию (bonuses, percent)
            discount_value - значение скидки
            tax_type - ставка НДС (const.VatRate)
            tax_sum - сумма налога, высчитанная продавцом
            payment_method - тип оплаты (const.PaymentMethod)
            payment_object - тип позиции (const.PaymentObject)
        """
        data = {
            'positionId': len(self.items),
            'name': title[:100],
            'itemCode': uid,
            'itemPrice': float(price),
            'quantity': {"value": quantity, "measure": measure},
            'tax': {'taxType': tax_type},
        }
        if discount_type is not None and discount_value is not None:
            data["discount"] = {
                'discountType': discount_type,
                'discountValue': discount_value
            }
        if tax_type is not None:
            data['tax']['taxType'] = tax_type
        if tax_sum is not None:
            data['tax']["taxSum"] = tax_sum
        data['itemAttributes'] = {
            "attributes": [
                {
                    "name": "paymentMethod",
                    "value": payment_method
                },
                {
                    "name": "paymentObject",
                    "value": payment_object
                }
            ]
        }
        if kwagrs:
            data.update(kwagrs)
        self.items.append(data)

    def to_data(self):
        data = {}
        if self.created_at:
            created_at_str = self.created_at.strftime(self.DATE_FORMAT)
            data['orderCreationDate'] = created_at_str
        if self.customer is not None:
            data['customerDetails'] = self.customer

        data['cartItems'] = {'items': self.items}
        return json.dumps(data)
