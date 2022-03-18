# Generated by Django 4.0.3 on 2022-03-18 02:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0008_remove_subscribe_subscription_period_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscribe',
            name='sub_type',
            field=models.CharField(choices=[('1', '1'), ('3', '3'), ('6', '6'), ('9', '9'), ('12', '12')], db_index=True, default=12, max_length=25, verbose_name='Тип подписки'),
        ),
    ]
