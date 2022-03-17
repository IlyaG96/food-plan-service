# Generated by Django 4.0.3 on 2022-03-17 09:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0006_remove_user_favorite_dishes_user_favorite_dishes_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.IntegerField(db_index=True, verbose_name='Стоимость заказа')),
                ('creation_date', models.DateTimeField(db_index=True, verbose_name='Дата создания заказа')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='tgbot.subscribe', verbose_name='Относится к подписке')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user', to='tgbot.user', verbose_name='Чек пользователя')),
            ],
            options={
                'verbose_name': 'Чек',
                'verbose_name_plural': 'Чеки',
            },
        ),
    ]
