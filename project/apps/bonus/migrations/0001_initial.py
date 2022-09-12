# Generated by Django 3.0.8 on 2022-08-26 14:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shop', '0001_initial'),
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BonusSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_deposit_percent', models.PositiveIntegerField(default=0, verbose_name='Бонусов за заказ в %')),
                ('order_withdraw_percent', models.PositiveIntegerField(default=0, verbose_name='Максимальное списание бонусов от заказа в %')),
                ('lifetime_bonuses', models.PositiveIntegerField(default=0, help_text='Если бонусы бессрочные, то оставить равным нулю', verbose_name='Дней до сгорания бонусов')),
                ('register_bonuses', models.PositiveIntegerField(default=0, verbose_name='Бонусов за регистрацию')),
                ('register_lifetime_bonuses', models.PositiveIntegerField(default=0, help_text='Если бонусы бессрочные, то оставить равным нулю', verbose_name='Дней до сгорания регистрационных бонусов')),
                ('first_order_bonuses', models.PositiveIntegerField(default=0, verbose_name='Бонусов за первый заказ')),
                ('first_order_lifetime_bonuses', models.PositiveIntegerField(default=0, help_text='Если бонусы бессрочные, то оставить равным нулю', verbose_name='Дней до сгорания бонусов за первый заказ')),
            ],
            options={
                'verbose_name': 'Настройки бонусной системы',
                'verbose_name_plural': 'Настройки бонусной системы',
            },
        ),
        migrations.CreateModel(
            name='BonusCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deposit_percent', models.PositiveIntegerField(blank=True, help_text='Процент бонусов начисляемый за товар данной категории', null=True, verbose_name='Бонусов за заказ в %')),
                ('withdraw_percent', models.PositiveIntegerField(blank=True, help_text='Процент бонусов списываемый за товар данной категории', null=True, verbose_name='Максимальное списание бонусов от заказа в %')),
                ('category', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bonus_category', to='catalog.Category')),
            ],
            options={
                'verbose_name': 'Бонус категории',
                'verbose_name_plural': 'Бонусы по категориям',
            },
        ),
        migrations.CreateModel(
            name='BonusAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.PositiveIntegerField(default=0, verbose_name='Баланс')),
                ('created_at', models.DateTimeField(verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(verbose_name='Дата последнего обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bonus_account', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Бонусный счет',
                'verbose_name_plural': 'Бонусные счета',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delta', models.IntegerField(verbose_name='Изменение баланса')),
                ('type', models.CharField(choices=[('CREATED', 'Создание аккаунта'), ('DEPOSITED', 'Начисление'), ('WITHDRAWN', 'Списание')], max_length=15, verbose_name='Тип операции')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Доступны до')),
                ('created_at', models.DateTimeField(verbose_name='Дата создания')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Комментарий')),
                ('debug_balance', models.IntegerField(verbose_name='Остаток на балансе')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='account_actions', to='bonus.BonusAccount', verbose_name='Аккаунт')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shop.Order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Действие бонусного счета',
                'verbose_name_plural': 'Действия бонусного счета',
            },
        ),
    ]
