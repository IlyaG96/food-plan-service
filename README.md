# food-plan-service
Сервис по подбору рецептов блюд на каждый день.
(в разработке)

## Настройки

### Подключите зависимости
```
pip install -r requirements.txt
```
### Подключите переменные окружения
Создайте файл `.env` в корневой директории рядом с `settings.py` и введите
```
TGBOT_TOKEN=<token>
PROVIDER_TOKEN=<token>
```
Где:
- TGBOT_TOKEN - токен телеграм-бота.  
- PROVIDER_TOKEN - токен провайдера для оплаты. (botfather/mybots/payments - выбрать юкассу, стоимость тестового заказа не более 1000 рублей!)
## Запуск бота
Для запуска бота введите
```
python manage.py bot
```

## Редактирование бота
Код бота располагается в `/tgbot/management/commands/bot.py`
