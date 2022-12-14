# Generated by Django 3.0.8 on 2022-06-21 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0014_seocontentfromlinks'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='seocontentfromlinks',
            options={'verbose_name': 'СЕО контент для страниц', 'verbose_name_plural': 'СЕО контент для страниц'},
        ),
        migrations.AddField(
            model_name='seocontentfromlinks',
            name='slugField',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Путь до страницы'),
        ),
    ]
