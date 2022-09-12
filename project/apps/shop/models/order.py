from django.conf import settings
from django.db import models
from django.core.cache import cache

from apps.catalog.models import Product, Category, Catalog, get_request
from apps.feedback.mailer import Mailer
from ..signals import order_created, order_paid
from apps.shop.models.endpoints import EndPoint
from apps.cart.models.base import get_gefest


class Order(models.Model):
    CREATED = "created"
    PROCESSING = "processing"
    WAITING = "waiting"
    TRANSFERED = "transfered"
    COMPLETED = "completed"
    CANCELED = "canceled"
    AWAITING = 'awaiting'
    PAID = 'paid'

    STATUS_CHOICES = (
        (CREATED, "Создан"),
        (PROCESSING, "В обработке"),
        (WAITING, "Ожидает в пункте самовывоза"),
        (TRANSFERED, "Передан в службу доставки"),
        (COMPLETED, "Выполнен"),
        (CANCELED, "Отменен"),
        (AWAITING, 'Ожидает оплаты'),
        (PAID, 'Оплачено')

    )

    EXCHANGE_STATUS_NOT = 'not'
    EXCHANGE_STATUS_EXPORTED = 'exported'
    EXCHANGE_STATUS_PROCESSING = 'process'

    EXCHANGE_STATUS_CHOICES = (
        (EXCHANGE_STATUS_NOT, 'Не выгружен'),
        (EXCHANGE_STATUS_EXPORTED, 'Выгружен'),
        (EXCHANGE_STATUS_PROCESSING, 'В процессе'),
    )

    domain = models.ForeignKey('domains.Domain', verbose_name="Домен", on_delete=models.CASCADE)
    oneclick = models.BooleanField('В 1 клик', default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='Пользователь',
        related_name='orders', on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        verbose_name='Статус', choices=STATUS_CHOICES,
        default=PROCESSING, max_length=20)
    name = models.CharField(verbose_name="ФИО", max_length=31)
    email = models.EmailField(verbose_name="Электронная почта")
    send = models.BooleanField(verbose_name="Отправлено", default=False)
    phone = models.CharField(verbose_name="Телефон", max_length=18)
    address = models.CharField(
        verbose_name='Адрес доставки', max_length=255, blank=True, default="")
    city = models.CharField(verbose_name='Город доставки',
                            max_length=127, blank=True, default="")
    total = models.DecimalField(
        verbose_name="Сумма заказа", max_digits=10, decimal_places=2)
    total_original = models.DecimalField(
        verbose_name="Сумма заказа без скидки", max_digits=10,
        decimal_places=2)
    bonuses_used = models.PositiveIntegerField(
        verbose_name='Использовано бонусов', default=0)

    paid = models.BooleanField(verbose_name="Оплачен", default=False)
    delivery = models.ForeignKey('configuration.Delivery', verbose_name="Доставка", blank=True,
                                 on_delete=models.SET_NULL, null=True)
    store = models.ForeignKey('stores.Store', verbose_name="Магазин", on_delete=models.SET_NULL, blank=True, null=True)
    comment = models.TextField('Комментарий к доставке', default="", blank=True)
    payment = models.ForeignKey('configuration.Payment', verbose_name="Оплата", blank=True, on_delete=models.SET_NULL,
                                null=True)
    # 1c
    status_export = models.CharField(
        "Выгрузка заказаов в 1С", default=EXCHANGE_STATUS_NOT,
        choices=EXCHANGE_STATUS_CHOICES, max_length=20)
    # dates
    created_at = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField(
        verbose_name='Дата последнего обновления', auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ №{self.id}'

    def get_total(self):
        """Расчет суммы заказа"""
        total = 0
        for item in self.items.all():
            total += item.total
        return total

    def get_items(self, select_related=False):
        """Получение всех элементов заказа"""
        items_manager = self.items
        if select_related:
            items_manager = items_manager.select_related('product')
        return items_manager.all()

    def create_items(self, cart):
        """Добавление элементов заказа"""
        cart_items = cart.items()
        if cart_items:
            # items = []
            for item in cart.items():
                price = item.product.get_storage_info().get("discount_price") or \
                        item.product.get_storage_info().get("price")
                element = OrderItem(order=self,
                                    product=item.product,
                                    price=price,
                                    domain=item.option,
                                    original_price=item.price,
                                    quantity=item.quantity).save()
                # items.append(element)
            # OrderItem.objects.bulk_create(items)

            self._created()
            return True
        print(f'======NO ITEMS {get_request().__dict__}')
        return False

    def _created(self):
        # сигнал создания заказа
        order_created.send(sender=self.__class__, instance=self)

    def pay(self):
        """Установка статуса оплачен"""
        self.paid = True
        self.status = self.PAID
        # self.send_notifications()
        self.save(update_fields=['paid', 'status'])
        # сигнал оплаты заказа
        order_paid.send(sender=self.__class__, instance=self)

    def get_category_receivers(self) -> list:
        emails = []
        categories = Category.objects.filter(products__id__in=self.items.values_list('product_id', flat=True))
        for category in categories:
            emails.extend(
                list(filter(None, category.get_ancestors(include_self=True).values_list('receivers__email', flat=True)))
            )
        return emails

    def get_admin_recipients(self, domain=None):

        if not domain:
            domain = get_request().domain

        emails = []

        categories = Category.objects.filter(products__id__in=self.items.values_list('product_id', flat=True))

        emails += self.get_category_receivers()

        for category in categories:
            emails += list(category.messages.filter(domain__exact=domain).values_list('recipients__email', flat=True))

        if self.store:
            emails += list(self.store.recipients.values_list('email', flat=True))

        if self.delivery:
            emails += list(self.delivery.recipients.values_list('email', flat=True))

        emails += ['ivan.mihailov@place-start.ru']

        return emails

    # def send_notifications(self):
    #     """Отправка уведомления о новом заказе"""
    #     request = get_request()
    #     Mailer.send(
    #         recipients=[self.email],
    #         template_name='shop/order_mail',
    #         context_data={'order': self, 'request': request})
    #
    # def send_admin_notifications(self, category_recipients=None):
    #     request = get_request()
    #     domain = request.domain
    #     emails = self.get_admin_recipients(domain)
    #     emails = list(set(emails))
    #     if emails:
    #         Mailer.send(
    #             recipients=emails,
    #             template_name='shop/order_mail',
    #             context_data={'order': self, 'is_admin': True, 'request': request})

    def send_notifications(self):
        """Отправка уведомления о новом заказе"""
        request = get_request()
        Mailer.render_message(
            recipients=[self.email],
            template_name='shop/order_mail',
            context_data={'order': self, 'request': request})

    def send_admin_notifications(self, category_recipients=[]):
        request = get_request()
        domain = request.domain
        emails = self.get_admin_recipients(domain)
        emails = list(set(emails))
        
        endpoints = EndPoint.objects.all()

        filtering_endpoints = []

        for endpoint in endpoints:
            if(endpoint.filter(Order.objects.filter(pk=self.pk)).count() > 0):
                filtering_endpoints.append(endpoint)

        for endpoint in filtering_endpoints:
            print("Email from endpoint", endpoint.store.email)
            emails.append(str(endpoint.store.email))

        emails += category_recipients

        print(f'======EMAILS {emails}')
        emails = list(set(emails))
        print(f'======EMAILS {emails}')

        #if emails:
        #    Mailer.render_message(
        #        recipients=emails,
        #        template_name='shop/order_mail',
        #        context_data={'order': self, 'is_admin': True, 'request': request})


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items',
                              on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, verbose_name="Товар", related_name='order_items',
        on_delete=models.PROTECT)
    domain = models.ForeignKey('domains.Domain', verbose_name="Город", on_delete=models.SET_NULL, blank=True, null=True)
    price = models.DecimalField(
        verbose_name="Стоимость товара", max_digits=10, decimal_places=2)
    # данное поле в случае если прикрутим бонусы или индивидуальные скидки
    original_price = models.DecimalField(
        verbose_name="Стоимость без учета скидки",
        max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(
        verbose_name="Количество", default=1)

    def __str__(self):
        return f'Элемент заказа {self.id}'

    @property
    def total(self):
        return float(self.price) * self.quantity

    def get_title(self):
        return '-'.join([item.title for item in [self.product.parent, self.product] if item])

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
