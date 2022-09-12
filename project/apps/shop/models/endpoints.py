from django import forms
from django.db import models
from django.db.models import Q
from django.apps import apps

from apps.catalog.models import Brand


class EndPoint(models.Model):
    store = models.ForeignKey('stores.Store', verbose_name="Магазин", blank=True, null=True, on_delete=models.CASCADE)
    domain = models.ForeignKey('domains.Domain', verbose_name="Домены", blank=True, null=True, on_delete=models.CASCADE)
    condition = models.TextField('Условие',
                                 help_text="В каждой строке применяется И, на каждую новую строку ИЛИ\n"
                                           "& - разделитель атрибутов,\n"
                                           "[store] - переменная выбранного магазина\n"
                                           "[domain] - переменная выбранного города\n")
    slug = models.CharField('Слаг', max_length=15, help_text='Строка между 1c_exchange и .py', unique=True)

    class Meta:
        ordering = ['slug']
        verbose_name = 'Эндпоинт'
        verbose_name_plural = 'Эндопоинты'

    def __str__(self):
        return self.slug

    def clean(self):
        filters = self.get_filters()
        if filters:
            Order = apps.get_model('shop', 'Order')
            try:
                Order.objects.filter(filters).count()
            except Exception as error:
                raise forms.ValidationError({'condition': f'Поле заполнено не верно! {error}'})
        else:
            raise forms.ValidationError({'condition': 'Поле заполнено не верно!'})

    def filter(self, qs):
        print("filters", self.get_filters())
        qs = qs.filter(self.get_filters())
        return qs

    def get_variable(self, value):
        value = value.replace('\r', '')
        if value == '[store]':
            return self.store
        if value == '[domain]':
            return self.domain
        return value

    def get_filters(self):
        q = Q()
        try:
            lines = self.condition.split('\n')
            for line in lines:
                attrs = line.split('&')
                q_and = Q()
                for attr in attrs:
                    key, value = attr.split('=')
                    value = self.get_variable(value)
                    q_and &= Q(**{f'{key}': value})
                q |= q_and
            if self.store.title == 'ул. Фучика, 9':
                q &= ~Q(items__product__brand__title='Гефест')
        except Exception:
            pass
        return q
