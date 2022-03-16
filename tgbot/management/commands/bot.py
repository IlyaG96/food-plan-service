from enum import Enum
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import (
    LabeledPrice,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    message
)
from telegram.ext import (CallbackContext,
                          CallbackQueryHandler,
                          CommandHandler,
                          ConversationHandler,
                          PreCheckoutQueryHandler,
                          Filters,
                          MessageHandler,
                          Updater)

from textwrap import dedent


class BotStates(Enum):
    GREET_USER = 1
    GET_USERNAME = 2
    GET_PHONENUMBER = 3
    GET_PORTIONS_SIZE = 4
    GET_PREFERENCES = 5
    GET_PORTIONS_QUANTITY = 6
    GET_SUBSCRIPTION_LENGTH = 7
    CHECK_ORDER = 8
    TAKE_PAYMENT = 9
    PRECHECKOUT = 10
    SUCCESS_PAYMENT = 11


def start(update, context):

    update.message.reply_text('Привет! Познакомимся? Я - бот, который облегчит тебе жизнь и спланирует рацион за тебя. '
                              'Пожалуйста, представься. Напиши имя и фамилию',
                              )

    return BotStates.GET_USERNAME


def get_user_phonenumber(update, context):

    if update.message.text != 'Назад ⬅':
        context.user_data['username'] = update.message.text

    phone_request_button = KeyboardButton('Передать контакт', request_contact=True)
    update.message.reply_text(
        'Мне понадобится номер телефона. Можно отправить свой номер из профиля или ввести вручную',
        reply_markup=ReplyKeyboardMarkup(
            [[phone_request_button, 'Назад ⬅']],
            resize_keyboard=True,
            input_field_placeholder='8-999-999-9999',
        ),
    )

    return BotStates.GET_PHONENUMBER


def get_portion_size(update, context):

    if update.message.text != 'Назад ⬅':
        if update.message.contact:
            phone_number = update.message.contact.phone_number
        else:
            phone_number = update.message.text
        context.user_data['phonenumber'] = phone_number

    # TODO replace from db
    keyboard = [[str(num) for num in range(1, 11)], ['Назад ⬅']]
    update.message.reply_text(
        'На какое количество человек рассчитывать блюдо?',
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         ),
    )
    return BotStates.GET_PORTIONS_SIZE


def get_preferences(update, context):
    if update.message.text != 'Назад ⬅':
        portion_size = update.message.text
        context.user_data['portion_size'] = portion_size

    keyboard = [['Мясоед',
                 'Предпочитаю рыбов',
                 'Убежденный веган',
                 'Всего и побольше',
                 'Низкокалорийная диета',
                 ], ['Назад ⬅']]
    # TODO replace from db
    # TODO если какая-то низкокалорийная диета, то можно добавить выбор блюд по калориям. Но это уже к фичам,
    #  наверное
    update.message.reply_text(
        'Есть какие-то предпочтения по диете?',
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         ),
    )

    return BotStates.GET_PREFERENCES


def get_portions_quantity(update, context):
    if update.message.text != 'Назад ⬅':
        preferences = update.message.text
        context.user_data['preferences'] = preferences
        # TODO replace from db
    keyboard = [[str(num) for num in range(1, 11)], ['Назад ⬅']]
    update.message.reply_text(
        'Сколько порций потребуется?',
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         ),
    )

    return BotStates.GET_PORTIONS_QUANTITY


def get_subscription_length(update, context):
    if update.message.text != 'Назад ⬅':
        portions_quantity = update.message.text
        context.user_data['portions_quantity'] = portions_quantity
        # TODO replace from db
    keyboard = [[str(num) for num in range(1, 13)], ['Назад ⬅']]
    update.message.reply_text(
        'На сколько месяцев Вы хотите оформить подписку?',
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         ),
    )
    return BotStates.GET_SUBSCRIPTION_LENGTH


def check_order(update, context):
    if update.message.text != 'Назад ⬅':
        subscription_length = update.message.text
        context.user_data['subscription_length'] = subscription_length

    username = context.user_data['username']
    phonenumber = context.user_data['phonenumber']
    portions_quantity = context.user_data['portions_quantity']
    portion_size = context.user_data['portion_size']
    preferences = context.user_data['preferences']
    subscription_length = context.user_data['subscription_length']

    price = int(portions_quantity)*int(portion_size)*int(subscription_length)
    # in test payment price should be less than 1000 rub!
    context.user_data['price'] = price

    # TODO get price from DB
    order = dedent(
        f'''
    Имя: {username}
    Номер телефона: {phonenumber}
    Количество порций: {portions_quantity}
    Размер порций: {portion_size}
    Предпочтения: {preferences}
    Длительность подписки: {subscription_length}
    Общая стоимость: {price}
    ''')

    keyboard = [['Перейти к оплате!', 'Назад ⬅']]
    update.message.reply_text(
        text=order,
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         ),
    )

    return BotStates.CHECK_ORDER


def take_payment(update, context):

    price = context.user_data['price']

    update.message.reply_text('Формирую счёт...',
                              reply_markup=ReplyKeyboardRemove())
    provider_token = settings.PROVIDER_TOKEN
    chat_id = update.message.chat_id
    title = 'Ваш заказ'
    description = f'Оплата вашего заказа стоимостью {price} рублей'
    payload = 'Custom-Payload'

    currency = 'RUB'
    prices = [LabeledPrice("Стоимость", price * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )

    return BotStates.PRECHECKOUT


def precheckout(update, _):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        query.answer(ok=True)

    return BotStates.SUCCESS_PAYMENT


def done(update, context):
    """End conversation."""

    update.message.reply_text(
        'До свидания!',
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def main():
    updater = Updater(settings.TGBOT_TOKEN)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={

            BotStates.GET_USERNAME: [
                MessageHandler(Filters.regex(r'[а-яА-Яa-zA-Z]{2,20}( )[а-яА-Яa-zA-Z]{2,20}$'),
                               get_user_phonenumber),
                MessageHandler(Filters.text, start)
            ],

            BotStates.GET_PHONENUMBER: [
                MessageHandler(Filters.regex(r'^\+?\d{1,3}?( |-)?\d{3}( |-)?\d{3}( |-)?\d{2}( |-)?\d{2}$'),
                               get_portion_size),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), start),
                MessageHandler(Filters.text, get_user_phonenumber)
            ],

            BotStates.GET_PORTIONS_SIZE: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), get_preferences),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_user_phonenumber),
                MessageHandler(Filters.text, get_portion_size)
            ],

            BotStates.GET_PREFERENCES: [
                MessageHandler(Filters.regex(r'[а-яА-Я ]{2,20}$'), get_portions_quantity),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_portion_size),
                MessageHandler(Filters.text, get_preferences)
            ],
            BotStates.GET_PORTIONS_QUANTITY: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), get_subscription_length),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_preferences),
                MessageHandler(Filters.text, get_portions_quantity)
            ],
            BotStates.GET_SUBSCRIPTION_LENGTH: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), check_order),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_portions_quantity),
                MessageHandler(Filters.text, get_subscription_length)
            ],
            BotStates.CHECK_ORDER: [
                MessageHandler(Filters.regex(r'Перейти к оплате!$'), take_payment),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_subscription_length),
                MessageHandler(Filters.text, check_order)
            ],
            BotStates.PRECHECKOUT: [
                PreCheckoutQueryHandler(precheckout),
            ],
            BotStates.SUCCESS_PAYMENT: [
                MessageHandler(Filters.successful_payment, done)
            ],

        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
        per_user=True,
        per_chat=False,
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        main()
