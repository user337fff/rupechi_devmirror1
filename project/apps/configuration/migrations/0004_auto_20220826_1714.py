# Generated by Django 3.0.8 on 2022-08-26 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0003_auto_20220826_1714'),
    ]

    operations = [
        migrations.AlterField(
            model_name='htmltag',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='configuration.HTMLGroup'),
        ),
    ]
