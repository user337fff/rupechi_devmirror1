# Generated by Django 3.0.8 on 2022-08-26 14:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stores', '__first__'),
        ('configuration', '__first__'),
        ('domains', '0015_auto_20220621_1513'),
        ('catalog', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oneclick', models.BooleanField(default=False, verbose_name='В 1 клик')),
                ('status', models.CharField(choices=[('created', 'Создан'), ('processing', 'В обработке'), ('waiting', 'Ожидает в пункте самовывоза'), ('transfered', 'Передан в службу доставки'), ('completed', 'Выполнен'), ('canceled', 'Отменен'), ('awaiting', 'Ожидает оплаты'), ('paid', 'Оплачено')], default='processing', max_length=20, verbose_name='Статус')),
                ('name', models.CharField(max_length=31, verbose_name='ФИО')),
                ('email', models.EmailField(max_length=254, verbose_name='Электронная почта')),
                ('send', models.BooleanField(default=False, verbose_name='Отправлено')),
                ('phone', models.CharField(max_length=18, verbose_name='Телефон')),
                ('address', models.CharField(blank=True, default='', max_length=255, verbose_name='Адрес доставки')),
                ('city', models.CharField(blank=True, default='', max_length=127, verbose_name='Город доставки')),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма заказа')),
                ('total_original', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сумма заказа без скидки')),
                ('bonuses_used', models.PositiveIntegerField(default=0, verbose_name='Использовано бонусов')),
                ('paid', models.BooleanField(default=False, verbose_name='Оплачен')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Комментарий к доставке')),
                ('status_export', models.CharField(choices=[('not', 'Не выгружен'), ('exported', 'Выгружен'), ('process', 'В процессе')], default='not', max_length=20, verbose_name='Выгрузка заказаов в 1С')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')),
                ('delivery', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='configuration.Delivery', verbose_name='Доставка')),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='domains.Domain', verbose_name='Домен')),
                ('payment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='configuration.Payment', verbose_name='Оплата')),
                ('store', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stores.Store', verbose_name='Магазин')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Заказ',
                'verbose_name_plural': 'Заказы',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость товара')),
                ('original_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Стоимость без учета скидки')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Количество')),
                ('domain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='domains.Domain', verbose_name='Город')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='shop.Order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='catalog.Product', verbose_name='Товар')),
            ],
            options={
                'verbose_name': 'Элемент заказа',
                'verbose_name_plural': 'Элементы заказа',
            },
        ),
        migrations.CreateModel(
            name='ExportLimiterOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_last_export', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата последнего экспорта')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EndPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.TextField(help_text='В каждой строке применяется И, на каждую новую строку ИЛИ\n& - разделитель атрибутов,\n[store] - переменная выбранного магазина\n[domain] - переменная выбранного города\n', verbose_name='Условие')),
                ('slug', models.CharField(help_text='Строка между 1c_exchange и .py', max_length=15, unique=True, verbose_name='Слаг')),
                ('domain', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='domains.Domain', verbose_name='Домены')),
                ('store', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='stores.Store', verbose_name='Магазин')),
            ],
            options={
                'verbose_name': 'Эндпоинт',
                'verbose_name_plural': 'Эндопоинты',
                'ordering': ['slug'],
            },
        ),
    ]
