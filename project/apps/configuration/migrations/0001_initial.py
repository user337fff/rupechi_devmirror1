# Generated by Django 3.0.8 on 2022-08-26 14:05

import apps.commons.models
import colorfield.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('feedback', '0008_auto_20220324_1943'),
        ('catalog', '__first__'),
        ('domains', '0015_auto_20220621_1513'),
        ('stores', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypePrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('price', 'Розница'), ('price_1', 'Контрагент 1'), ('price_2', 'Контрагент 2'), ('price_3', 'Контрагент 3')], default='price', max_length=125, unique=True, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Тип цены',
                'verbose_name_plural': 'Типы цен',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta_keywords', models.TextField(blank=True, default='', verbose_name='Meta Keywords')),
                ('name', models.CharField(max_length=127, verbose_name='Наименование сайта')),
                ('logo', models.ImageField(blank=True, help_text='Размер 270x80', null=True, upload_to='images/configuration/logo/', verbose_name='Лого')),
                ('logo_email', models.ImageField(blank=True, null=True, upload_to='images/logo/mail/', verbose_name='Лого для уведомлений')),
                ('favicon', models.ImageField(blank=True, null=True, upload_to='images/configuration/logo/favicon/', verbose_name='Фавикон')),
                ('meta_title', models.CharField(blank=True, default='', max_length=125, verbose_name='Название по умолчанию')),
                ('meta_description', models.TextField(blank=True, default='', verbose_name='Описание по умолчанию')),
                ('color_scheme', colorfield.fields.ColorField(default='#006EFF', help_text='HEX color, as #RRGGBB', max_length=7, verbose_name='Цветовая схема сайта')),
                ('color_scheme_alpha', models.CharField(blank=True, default='rgba(0, 110, 255, 0.6)', max_length=50, verbose_name='Цветовая схема c alpha')),
                ('color_scheme_dark', models.CharField(blank=True, default='#000CD4', max_length=7, verbose_name='Цветовая схема затемнение')),
                ('address', models.CharField(blank=True, default='', max_length=255, verbose_name='Адрес')),
                ('email', models.EmailField(blank=True, default='', max_length=254, verbose_name='Email')),
                ('phone', models.CharField(blank=True, default='', max_length=31, verbose_name='Номер телефона')),
                ('extra_phones', models.CharField(blank=True, default='', help_text='Введите номера через запятую', max_length=255, verbose_name='Дополнительные номера телефонов')),
                ('lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Координата X на карте')),
                ('lon', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name='Координата Y на карте')),
                ('custom_field_title', models.CharField(blank=True, default='', max_length=127, verbose_name='Пользовательское поле')),
                ('custom_field_value', models.CharField(blank=True, default='', max_length=127, verbose_name='Значение пользовательского поля')),
                ('requisites', models.FileField(blank=True, null=True, upload_to='files/configuration/requisites/', verbose_name='Реквизиты')),
                ('company_name', models.CharField(blank=True, default='', max_length=127, verbose_name='Название компании')),
                ('legal_address', models.CharField(blank=True, default='', max_length=127, verbose_name='Юридический адрес')),
                ('domain', models.CharField(blank=True, default='', max_length=63, verbose_name='Домен')),
                ('vkontakte', models.CharField(blank=True, default='', max_length=127, verbose_name='Ссылка на ВК группу')),
                ('facebook', models.CharField(blank=True, max_length=127, verbose_name='Ссылка на fb группу')),
                ('instagram', models.CharField(blank=True, max_length=127, verbose_name='Ссылка на instagram')),
                ('telegram', models.CharField(blank=True, max_length=127, verbose_name='Ссылка на telegram')),
                ('twitter', models.CharField(blank=True, max_length=127, verbose_name='Ссылка на twitter')),
                ('youtube', models.CharField(blank=True, max_length=127, verbose_name='Ссылка на youtube')),
                ('odnoklassniky', models.CharField(blank=True, max_length=127, verbose_name='Ссылка на Одноклассники')),
                ('banner_text', models.CharField(blank=True, default='', max_length=255, verbose_name='Текст баннера в сайдбаре')),
                ('banner_img', models.ImageField(blank=True, null=True, upload_to='images/configuration/banner/', verbose_name='Изображение на баннере в сайдбаре')),
                ('card_payment', models.TextField(blank=True, default='', verbose_name="Текст 'доставка' в карточке товара")),
                ('card_shipping', models.TextField(blank=True, default='', verbose_name="Текст 'доставка' в карточке товара")),
                ('discount', models.PositiveSmallIntegerField(default=0, verbose_name='Процент скидки онлайн заказа')),
                ('attr_chimney', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.ProductAttribute', verbose_name='Атрибут')),
                ('attr_second', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='second_attr', to='catalog.ProductAttribute', verbose_name='Второй атрибут')),
                ('discount_domain', models.ManyToManyField(blank=True, null=True, to='domains.Domain', verbose_name='Домены для скидок')),
                ('recipients', models.ManyToManyField(blank=True, to='feedback.Recipient', verbose_name='Получатели')),
                ('type_price', models.ManyToManyField(blank=True, to='configuration.TypePrice', verbose_name='Тип цен')),
            ],
            options={
                'verbose_name': 'Настройки сайта',
                'verbose_name_plural': 'Настройки сайта',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=125, verbose_name='Название')),
                ('sort', models.PositiveSmallIntegerField(default=0, verbose_name='Сортировка')),
                ('domain', models.ManyToManyField(blank=True, to='domains.Domain', verbose_name='Домены')),
                ('type_price', models.ManyToManyField(blank=True, to='configuration.TypePrice', verbose_name='Тип цен')),
            ],
            options={
                'verbose_name': 'Способ оплаты',
                'verbose_name_plural': 'Способы оплаты',
                'ordering': ['sort'],
            },
        ),
        migrations.CreateModel(
            name='IndexSlide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('webp_image', models.TextField(blank=True, null=True, verbose_name='Полный путь до webp')),
                ('webp_hash_image', models.TextField(blank=True, null=True, verbose_name='Хэш для webp')),
                ('webp_image_s', models.TextField(blank=True, null=True, verbose_name='Полный путь до webp_small')),
                ('webp_hash_image_s', models.TextField(blank=True, null=True, verbose_name='Хэш для webp_small')),
                ('webp_image_m', models.TextField(blank=True, null=True, verbose_name='Полный путь до webp_medium')),
                ('webp_hash_image_m', models.TextField(blank=True, null=True, verbose_name='Хэш для webp_medium')),
                ('webp_image_l', models.TextField(blank=True, null=True, verbose_name='Полный путь до webp_large')),
                ('webp_hash_image_l', models.TextField(blank=True, null=True, verbose_name='Хэш для webp_large')),
                ('image', models.ImageField(blank=True, null=True, upload_to=apps.commons.models.image_directory_path, verbose_name='Изображение')),
                ('image_md5', models.CharField(blank=True, default='', help_text='Заполняется автоматически', max_length=63, verbose_name='Хэш изображения')),
                ('link', models.CharField(blank=True, default='', max_length=127, verbose_name='Ссылка')),
                ('sort', models.PositiveSmallIntegerField(default=0, verbose_name='Сортировка')),
                ('domain', models.ManyToManyField(to='domains.Domain', verbose_name='Домены')),
            ],
            options={
                'verbose_name': 'Элемент слайдера',
                'verbose_name_plural': 'Слайдер',
                'ordering': ['sort'],
            },
        ),
        migrations.CreateModel(
            name='Delivery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=125, verbose_name='Название')),
                ('id_1c', models.CharField(blank=True, default='', help_text='Для выгрузки заказов', max_length=125, verbose_name='id 1c')),
                ('subtitle', models.CharField(blank=True, default='', max_length=125, verbose_name='Описание')),
                ('selection', models.BooleanField(default=False, verbose_name='Выделение описания')),
                ('sort', models.PositiveSmallIntegerField(default=0, verbose_name='Сортировка')),
                ('domain', models.ManyToManyField(blank=True, to='domains.Domain', verbose_name='Домены')),
                ('recipients', models.ManyToManyField(blank=True, to='feedback.Recipient', verbose_name='Получатели')),
                ('stores', models.ManyToManyField(blank=True, to='stores.Store', verbose_name='Магазины')),
                ('type_price', models.ManyToManyField(blank=True, to='configuration.TypePrice', verbose_name='Тип цен')),
            ],
            options={
                'verbose_name': 'Способ доставки',
                'verbose_name_plural': 'Способы доставки',
                'ordering': ['sort'],
            },
        ),
    ]
