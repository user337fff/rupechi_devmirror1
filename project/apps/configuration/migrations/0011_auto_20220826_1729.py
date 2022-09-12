# Generated by Django 3.0.8 on 2022-08-26 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0010_auto_20220826_1728'),
    ]

    operations = [
        migrations.AlterField(
            model_name='htmltag',
            name='bottomTagContent',
            field=models.TextField(blank=True, max_length=2500, verbose_name='Нижний контент элемента'),
        ),
        migrations.AlterField(
            model_name='htmltag',
            name='topTagContent',
            field=models.TextField(blank=True, max_length=2500, verbose_name='Верхний контент элемента'),
        ),
    ]
