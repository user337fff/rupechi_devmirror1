# Generated by Django 3.0.8 on 2021-04-26 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='id_price',
            field=models.UUIDField(blank=True, null=True, verbose_name='id розничной цены'),
        ),
    ]
