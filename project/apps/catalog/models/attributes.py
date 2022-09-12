import traceback
from django.db import models
from apps.catalog.utils import create_cyrillic_slug

class ProductAttribute(models.Model):
    DICT = "dict"
    NUMBER = "number"
    TYPE_CHOICES = (
        (DICT, 'Справочник'),
        (NUMBER, 'Числовой'),
    )

    title = models.CharField(verbose_name='Название', max_length=557)
    slug = models.SlugField(verbose_name='Слаг', max_length=557)
    type = models.CharField(
        verbose_name='Тип атрибута', max_length=7,
        choices=TYPE_CHOICES, default=DICT)
    position = models.PositiveIntegerField(verbose_name='Позиция', default=0)
    brand_position = models.PositiveIntegerField(verbose_name='Позиция для производителей', default=0)
    # import
    id_1c = models.UUIDField(
        verbose_name='Идентификатор 1С', blank=True, null=True, unique=True,
        help_text='Заполняется автоматически')
    is_collapsed = models.BooleanField('Свернут по умолчанию', default=True)
    visible_on_attrs = models.BooleanField('Показывать в атрибутах', default=True)
    visible_on_brand = models.BooleanField('Показывать в производителях', default=False)


    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if(not self.slug):
            self.slug = create_cyrillic_slug(self.title)
            try:
                super().save(*args, **kwargs)
            except:
                traceback.print_exc()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Атрибут'
        verbose_name_plural = 'Атрибуты'
        ordering = ('position',)


class AttributeValue(models.Model):
    value = models.CharField(
        verbose_name='Значение', max_length=527, db_index=True)
    slug = models.SlugField(verbose_name='Слаг', max_length=527)
    # import
    id_1c = models.UUIDField(
        verbose_name='Идентификатор 1С', blank=True, null=True, unique=True,
        help_text='Заполняется автоматически')

    def __str__(self):
        return self.value

    class Meta:
        ordering = ['value']
        verbose_name = 'Значение атрибута'
        verbose_name_plural = 'Справочник атрибутов'


class AttributeProducValue(models.Model):
    attribute = models.ForeignKey(
        ProductAttribute, on_delete=models.CASCADE,
        related_name='attribute_values')
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, related_name='product_attributes')

    value_dict = models.ForeignKey(
        AttributeValue, verbose_name='Значение из справочника',
        blank=True, null=True, db_index=True, on_delete=models.CASCADE)
    value_number = models.FloatField(verbose_name='Числовое значение',
                                     blank=True, null=True, db_index=True)
    position = models.PositiveIntegerField(verbose_name='Позиция', default=0)

    def __str__(self):
        return str(self.value)

    def _get_value(self):
        value = getattr(self, f'value_{self.attribute.type}')
        return value

    def _set_value(self, new_value):
        attr_name = f'value_{self.attribute.type}'
        if self.attribute.type == self.attribute.DICT:
            new_value, _created = AttributeValue.objects.get_or_create(
                value=new_value)
        elif self.attribute.type == self.attribute.NUMBER:
            new_value = float(new_value)
        setattr(self, attr_name, new_value)
        return

    value = property(_get_value, _set_value)

    class Meta:
        verbose_name = 'Атрибут-Товар-Значение'
        verbose_name_plural = 'Атрибут-Товар-Значение'
        ordering = ('position', 'attribute__position')
        # ordering = ('position',)


class ReplaceAttr(models.Model):
    replace_slug = models.CharField('Переменная', max_length=125, unique=True)
    attribute = models.ForeignKey('catalog.ProductAttribute', on_delete=models.CASCADE, verbose_name="Атрибут")

    class Meta:
        ordering = ['id']
        verbose_name = 'Переменная для описания'
        verbose_name_plural = 'Переменные для описания'

    def __str__(self):
        return self.slug + ' - ' + self.attribute.__str__()

    @property
    def slug(self):
        return f'||{self.replace_slug}||'
