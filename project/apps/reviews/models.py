from django.db import models
from django.utils.timezone import now

from apps.commons.models import ImageModel


class ReviewQuerySet(models.QuerySet):

    def active(self):
        return self.filter(is_active=True)

    def without_product(self):
        return self.filter(product=None)


class Review(ImageModel, models.Model):
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, verbose_name="Продукт", blank=True,
                                null=True, related_name='reviews')
    is_active = models.BooleanField('Активность', default=True)
    author = models.CharField('Автор', max_length=125)
    email = models.EmailField('Email', blank=True, default="")
    message = models.TextField('Сообщение')
    date_created = models.DateTimeField('Дата создания', default=now)
    sort = models.PositiveSmallIntegerField('Сортировка', default=0)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ['sort', '-date_created']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.author}: {self.message[:75]}'

    def get_image(self):
        if self.image:
            return self.image
        return {'url': '/static/images/no_user.png'}
