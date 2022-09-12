# Generated by Django 3.0.8 on 2021-05-28 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0003_auto_20210506_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='seo_description_category',
            field=models.TextField(blank=True, default='', verbose_name='SEO Описание для категорий'),
        ),
        migrations.AddField(
            model_name='domain',
            name='seo_description_product',
            field=models.TextField(blank=True, default='', verbose_name='SEO Описание для продукта'),
        ),
    ]