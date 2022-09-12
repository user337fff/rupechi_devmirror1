from django.db import models
from django.utils.translation import ugettext_lazy as _


class Recipient(models.Model):
    email = models.EmailField(_(u'email'), unique=True)

    class Meta:
        verbose_name = 'Получатель'
        verbose_name_plural = 'Получатели'

    def __str__(self):
        return self.email


class RecipientMixin(models.Model):
    recipients = models.ManyToManyField('feedback.Recipient', verbose_name="Получатели", blank=True, symmetrical=False)

    class Meta:
        abstract = True


class Mail(RecipientMixin, models.Model):
    class TypeChoice(models.TextChoices):
        REGISTER = 'register', 'Регистрация пользователя'
        ONECLICK = 'oneclick', 'Заказ в 1 клик'
        BOILER = 'boiler', 'Монтаж котла'
        FURNACE = 'furnace', 'Монтаж печи'
        FIREPLACE = 'fireplace', 'Монтаж камина'
        CHIMNEY = 'chimney', 'Монтаж дымохода'
        COOP = 'coop', 'Сотрудничество'
        SUBSCRIBE = 'subscribe', 'Подписка'
        COUPON = 'coupon', 'Получить купон'
        CHEAPER = 'cheaper', 'Нашли дешевле'
        IN_STOCK = 'in_stock', 'Сообщить о поступлении'

    type = models.CharField('Тип', default=TypeChoice.SUBSCRIBE, max_length=25, choices=TypeChoice.choices)
    domains = models.ManyToManyField('domains.Domain', verbose_name="Домены", blank=True, symmetrical=False)

    class Meta:
        ordering = ['type']
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

    def __str__(self):
        return self.get_type_display()

    def cities(self):
        return ', '.join([domain.name for domain in self.domains.iterator()])

    cities.short_description = 'Города'
    cities.admin_order_field = 'domains'


class Emails(models.Model):
    recipients = models.TextField(verbose_name='Получатели')
    from_mail = models.CharField(verbose_name='Отправитель', max_length=255)
    subject = models.CharField(verbose_name='Тема сообщения', max_length=255)
    message = models.TextField(verbose_name='html сообщения')
    text = models.TextField(verbose_name='Текст сообщения')
