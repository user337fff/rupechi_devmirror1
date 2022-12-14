# Generated by Django 3.0.8 on 2022-08-26 14:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('catalog', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=63, unique=True, verbose_name='Заголовок')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='Позиция')),
            ],
            options={
                'verbose_name': 'Опция',
                'verbose_name_plural': 'Опции',
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='OptionValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(db_index=True, max_length=63, verbose_name='Значение')),
                ('position', models.PositiveIntegerField(default=0, verbose_name='Позиция')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='option_values', to='product_options.Option')),
            ],
            options={
                'verbose_name': 'Значение опции',
                'verbose_name_plural': 'Значения Опций',
                'ordering': ('position',),
            },
        ),
        migrations.CreateModel(
            name='ProductOption',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Цена')),
                ('old_price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Старая цена')),
                ('stock', models.PositiveIntegerField(default=0, verbose_name='Остаток на складе')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата последнего обновления')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_options', to='catalog.Product')),
                ('value', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='value_product_options', to='product_options.OptionValue', verbose_name='Значение')),
            ],
            options={
                'verbose_name': 'Опция товара',
                'verbose_name_plural': 'Опции товаров',
            },
        ),
    ]
