import decimal
from django.apps import apps
from django.http import JsonResponse
from django.views.generic.base import View
from django.views.generic.edit import ProcessFormView
from django.urls import reverse

from apps.cart.models import CartItem, get_cart
from apps.cart.models.unauth_cart import UnauthCart
from apps.feedback.mailer import Mailer
from apps.feedback.models import Mail
from apps.configuration.models import Settings
from apps.shop.models import Order, OrderItem
from apps.catalog.models import Product, InStockNotification
from apps.cart.models.base import get_cart, get_gefest
from apps.domains.models import Domain


class MessageRecipientsMixin(View):
    type_message = None
    directory = ''
    mail = None
    replace_form = False
    message = ''
    description = ''
    order = None

    def get_mail(self):
        self.mail = Mail.objects.filter(type=self.type_message, domains__exact=self.request.domain).first()
        return self.mail

    def get_recipients(self, email=[]):
        if self.get_mail():
            emails = list(self.mail.recipients.values_list('email', flat=True))
        emails.extend(email)
        return emails

    def post(self, request, *args, **kwargs):
        response = {}
        context = self.request.POST.dict()
        send = self.send(context)
        if send:
            response['success'] = True
            for key in ['replace_form', 'message', 'description']:
                response[key] = getattr(self, key)
            response['mail'] = self.mail.type
            print('======SEND SUCCESS 2')
        if self.order:
            ecommerceListProducts = []

            orderProducts = self.order.items.all()
            for orderProduct in orderProducts:
                obj = {
                    "name": str(orderProduct.product.title),
                    "id": int(orderProduct.product.id),
                    "price": float(orderProduct.price),
                    "brand": str(orderProduct.product.brand),
                    "category": str(orderProduct.product.category),
                    "quantity": int(orderProduct.quantity),
                }

                if(not obj['brand']):
                    obj.pop("brand")

                ecommerceListProducts.append(obj)

            response["ecommerce_products"] = ecommerceListProducts
            response["order_id"] = int(self.order.id)
            response['redirect'] = f"{reverse('shop:order')}?success=1&order={self.order.id}"
        return JsonResponse(response)

    def get_extra_data(self):
        return {}

    def send(self, context=None):
        context = context or {}
        context.update(self.get_extra_data())
        emails = self.get_recipients()
        context.update({'mail': self.mail, 'request': self.request})
        emails = list(set(emails))
        print(f'====CHECK SEND MESSAGE {emails}')
        Mailer.render_message(
            recipients=emails,
            template_name=f'feedback/{self.directory}',
            context_data=context)
        return True


class GiveCoupon(MessageRecipientsMixin, ProcessFormView, View):
    type_message = Mail.TypeChoice.COUPON
    directory = 'coupon'
    message = 'Заявка успешно отправлена'
    replace_form = True

    def get_extra_data(self):
        cart = get_cart(self.request)

        print("Полученная карточка равна")
        print(type(cart))

        if(type(cart) == UnauthCart):
            cart_items = cart.items()
        else:
            cart_items = CartItem.objects.filter(cart=cart)

        return {'items': cart_items}


class CalcMounting(MessageRecipientsMixin, ProcessFormView, View):
    directory = 'mounting'
    replace_form = True
    message = 'Спасибо за заявку!'
    description = 'Наш специалист свяжется<br>с вами в течение 24 часов.'

    def get_mail(self):
        device = self.request.POST.get('device')
        choices = {
            'Котел': Mail.TypeChoice.BOILER,
            'Печь': Mail.TypeChoice.FURNACE,
            'Камин': Mail.TypeChoice.FIREPLACE,
            'Дымоход': Mail.TypeChoice.CHIMNEY,
        }
        self.mail = Mail.objects.filter(domains__exact=self.request.domain, type=choices.get(device)).first()
        return self.mail


class SubscribeView(MessageRecipientsMixin, ProcessFormView, View):
    directory = 'subscribe'
    type_message = Mail.TypeChoice.SUBSCRIBE
    replace_form = True
    message = 'Подписка успешно оформлена'


class CoopView(MessageRecipientsMixin, ProcessFormView, View):
    directory = 'coop'
    message = 'Спасибо за заявку!'
    description = 'Ваш персональный менеджер скоро свяжется с вами'
    replace_form = True
    type_message = Mail.TypeChoice.COOP

    def get_mail(self):
        domain = Domain.objects.get(name=self.request.POST.get('city'))
        self.mail = Mail.objects.filter(type=self.type_message, domains__exact=domain).first()
        return self.mail

    def get_extra_data(self):
        """Собираем контекст для отправки сообщения менеджеру"""
        email = self.request.POST.get('email')
        organization = self.request.POST.get('title')
        fullname = self.request.POST.get('fullname')
        inn = self.request.POST.get('inn')
        field_of_activity = self.request.POST.get('field_of_activity')
        city = self.request.POST.get('city')
        phone = self.request.POST.get('phone')
        context = {'email': email,
                   'organization': organization,
                   'name': fullname,
                   'inn': inn,
                   'field_of_activity': field_of_activity,
                   'city': city,
                   'phone': phone}
        
        """Отправляем сообщение оптовому клиенту"""
        Mailer.render_message(
            recipients=[email],
            template_name='feedback/client_coop',
            context_data={'city': city}
        )
        return context


class OneClickView(MessageRecipientsMixin, ProcessFormView, View):
    directory = 'oneclick'
    type_message = Mail.TypeChoice.ONECLICK
    order_id = None

    def get_recipients(self):
        emails = []
        order = Order.objects.get(id=self.order_id)
        emails += order.get_admin_recipients()
        if self.request.domain.domain == 'spb.rupechi.ru':
            if get_gefest(get_cart(self.request)):
                emails.append('tlcub@rupechi.ru')
            else:
                emails.append('kubatura@rupechi.ru')
        emails = list(set(emails))
        return super().get_recipients(email=emails)

    def get_extra_data(self):
        user = self.request.user if self.request.user.is_authenticated else None
        data = self.request.POST.dict()
        product = data.pop('product', None)
        quantity = decimal.Decimal(data.pop('quantity') or 1)
        order = Order(user=user, oneclick=True, **data)
        data = {'order': order}
        cart = None
        if not product:
            cart = get_cart(self.request)
            order.total = cart.total
            order.total_original = cart.total_without_discount
            order.city = self.request.domain.name
            order.domain = self.request.domain
            order.save()
            # добавление элементов заказа
            order.create_items(cart)
        else:
            product = Product.objects.get(id=product)
            info = product.get_storage_info()
            price = info.get('discount_price') or info.get('old_price') or info.get('price')
            order.total = price * quantity
            order.total_original = info.get('price') * quantity
            order.city = self.request.domain.name
            order.domain = self.request.domain
            order.save()
            OrderItem.objects.create(order=order, product=product, domain=self.request.domain,
                                     price=price, original_price=info.get('price'), quantity=quantity)
        data.update({'items': order.get_items()})
        data.update({'logo': Settings.get_settings().logo_email})
        data.update({'total': order.get_total()})
        try:
            if order.total < 1:
                print(f'=====DEBUG ONECLICK ORDER apps/feedback/views.py line 143 '
                      f'{cart.__dict__}, {data}, {order.get_items()}')
        except:
            print('=====DEBUG ONECLICK ORDER apps/feedback/views.py ERROR!!!')
        order.send_notifications()
        order.get_admin_recipients()
        if cart:
            # очистка корзины
            cart.clear()
        self.order = order
        self.order_id = order.id

        print(data)

        return data


class CheaperView(MessageRecipientsMixin, ProcessFormView, View):
    directory = 'cheaper'
    type_message = Mail.TypeChoice.CHEAPER
    message = 'Заявка успешно отправлена'

    def get_extra_data(self):
        product = self.request.POST.get('product')
        Product = apps.get_model('catalog', 'Product')
        product = Product.objects.get(id=product)
        product_price = product.prices.get(domain=self.request.domain).price
        response = {'request': self.request}
        if product:
            response.update({'product': product, 'product_price': product_price})
        return response


class InStockView(MessageRecipientsMixin, ProcessFormView, View):
    directory = 'in_stock'
    type_message = Mail.TypeChoice.IN_STOCK
    description = 'Мы уведомим вас о поступлении товара по почте'
    replace_form = True

    def get_extra_data(self):
        data = self.request.POST
        product = Product.objects.get(id=data.get('product'))
        response = dict(
            request=self.request,
            product=product,
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone')
        )
        InStockNotification(
            user_email=data.get('email'),
            domain=self.request.domain,
            product=product
        ).save()
        return response
