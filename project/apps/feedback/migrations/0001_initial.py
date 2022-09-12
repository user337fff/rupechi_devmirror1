# Generated by Django 3.0.8 on 2021-04-12 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Recipient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
            ],
            options={
                'verbose_name': 'recipient',
                'verbose_name_plural': 'recipients',
            },
        ),
    ]
