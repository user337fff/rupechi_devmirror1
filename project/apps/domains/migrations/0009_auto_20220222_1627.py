# Generated by Django 3.0.8 on 2022-02-22 13:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0008_auto_20220222_1625'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='domain',
            name='meta_product_meta_description',
        ),
        migrations.RemoveField(
            model_name='domain',
            name='meta_product_title',
        ),
    ]
