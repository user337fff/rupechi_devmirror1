# Generated by Django 3.0.8 on 2022-06-21 12:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0013_domain_name_dat'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeoContentFromLinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, default='', max_length=200, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, default='', verbose_name='Описание')),
                ('keywords', models.TextField(blank=True, default='', verbose_name='Клюечевые слова')),
                ('domainSettings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='domains.Domain', verbose_name='Настройки домена')),
            ],
        ),
    ]
