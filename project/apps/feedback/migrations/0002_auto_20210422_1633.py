# Generated by Django 3.0.8 on 2021-04-22 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0001_initial'),
        ('feedback', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='recipient',
            options={'verbose_name': 'Получатель', 'verbose_name_plural': 'Получатели'},
        ),
        migrations.AlterField(
            model_name='recipient',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='email'),
        ),
        migrations.CreateModel(
            name='Mail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('register', 'Регистрация пользователя'), ('oneclick', 'Заказ в 1 клик'), ('boiler', 'Монтаж котла'), ('furnace', 'Монтаж печи'), ('fireplace', 'Монтаж камина'), ('chimney', 'Монтаж дымохода'), ('coop', 'Сотрудничество'), ('subscribe', 'Подписка'), ('error', 'Ошибка'), ('coupon', 'Получить купон')], default='subscribe', max_length=25, verbose_name='Тип')),
                ('domains', models.ManyToManyField(blank=True, to='domains.Domain', verbose_name='Домены')),
                ('recipients', models.ManyToManyField(blank=True, to='feedback.Recipient', verbose_name='Получатели')),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
                'ordering': ['type'],
            },
        ),
    ]