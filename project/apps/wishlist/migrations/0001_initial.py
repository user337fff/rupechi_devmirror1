# Generated by Django 3.0.8 on 2022-08-26 14:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist_items', to='catalog.Product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wishlist_products', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Элемент избранных товаров',
                'verbose_name_plural': 'Элементы избранных товаров',
                'ordering': ['id'],
            },
        ),
    ]