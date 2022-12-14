# Generated by Django 3.0.8 on 2021-04-23 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_auto_20210422_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='type',
            field=models.CharField(choices=[('register', 'Регистрация пользователя'), ('oneclick', 'Заказ в 1 клик'), ('boiler', 'Монтаж котла'), ('furnace', 'Монтаж печи'), ('fireplace', 'Монтаж камина'), ('chimney', 'Монтаж дымохода'), ('coop', 'Сотрудничество'), ('subscribe', 'Подписка'), ('coupon', 'Получить купон')], default='subscribe', max_length=25, verbose_name='Тип'),
        ),
    ]
