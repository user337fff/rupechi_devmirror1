# Generated by Django 3.0.8 on 2022-02-22 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0010_auto_20220222_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domain',
            name='meta_product_meta_description',
            field=models.TextField(blank=True, default='', help_text='\n                                        Данное поле заполнятеся только для отдельных товаров разделов\n                                        ', verbose_name='Meta product Description'),
        ),
    ]