# Generated by Django 3.0.8 on 2022-03-24 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0007_auto_20211202_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='type',
            field=models.CharField(choices=[('register', 'Регистрация пользователя'), ('oneclick', 'Заказ в 1 клик'), ('boiler', 'Монтаж котла'), ('furnace', 'Монтаж печи'), ('fireplace', 'Монтаж камина'), ('chimney', 'Монтаж дымохода'), ('coop', 'Сотрудничество'), ('subscribe', 'Подписка'), ('coupon', 'Получить купон'), ('cheaper', 'Нашли дешевле'), ('in_stock', 'Сообщить о поступлении')], default='subscribe', max_length=25, verbose_name='Тип'),
        ),
    ]