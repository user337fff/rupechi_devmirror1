# Generated by Django 3.0.8 on 2022-02-22 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0009_auto_20220222_1627'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='meta_product_meta_description',
            field=models.TextField(blank=True, default='', help_text='\n                                        Данное поле заполнятеся только для отдельных товаров разделов\n                                        ||object|| - Заголовок объекта\n                                        ||site|| - Название сайта\n                                        ||city|| - Название города текущего поддомена\n                                        ||city1|| - Название города текущего поддомена в предложном падеже\n                                        ||price|| - Цена товара\n                                        ', verbose_name='Meta product Description'),
        ),
        migrations.AddField(
            model_name='domain',
            name='meta_product_title',
            field=models.CharField(blank=True, default='', help_text='Данный залоговок необходимтолько для альтернативного сео товара данной категории', max_length=255, verbose_name='SEO заголовок для товаров категории'),
        ),
    ]
