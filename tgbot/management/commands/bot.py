from textwrap import dedent
from enum import Enum
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import (
    ReplyKeyboardMarkup,
    ReplyMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
    Update,
    message
)
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


class BotStates(Enum):
    GREET_USER = 1
    GET_USERNAME = 2
    GET_PHONENUMBER = 3
    GET_PORTIONS_SIZE = 4
    GET_PREFERENCES = 5
    GET_PORTIONS_QUANTITY = 6
    GET_SUBSCRIPTION_LENGTH = 7
    TAKE_PAYMENT = 8
    CHECK_PAYMENT = 9


def start(update, context):

    update.message.reply_text('Привет! Познакомимся? Я - бот, который облегчит тебе жизнь и спланирует рацион за тебя. '
                              'Пожалуйста, представься. Напиши имя и фамилию',
                              )

    return BotStates.GET_USERNAME


def get_user_phonenumber(update, context):
    context.user_data['name'] = update.message.text
    phone_request_button = KeyboardButton('Передать контакт', request_contact=True)
    update.message.reply_text(
        'Мне понадобится номер телефона. Можно отправить свой номер из профиля или ввести вручную',
        reply_markup=ReplyKeyboardMarkup(
            [[phone_request_button]],
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
    pass


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
                MessageHandler(Filters.regex(r'[а-яА-Я]{2,20}( )[а-яА-Я]{2,20}$'),
                               get_user_phonenumber),
                MessageHandler(Filters.text, start)
            ],

            BotStates.GET_PHONENUMBER: [
                MessageHandler(Filters.regex(r'^\+?\d{1,3}?( |-)?\d{3}( |-)?\d{3}( |-)?\d{2}( |-)?\d{2}$'),
                               get_portion_size),
                MessageHandler(Filters.text, get_user_phonenumber)
            ],

            BotStates.GET_PORTIONS_SIZE: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), get_preferences),
                MessageHandler(Filters.text, get_portion_size)
            ],

            BotStates.GET_PREFERENCES: [
                MessageHandler(Filters.regex(r'[а-яА-Я]{2,15}$'), get_subscription_length),
                MessageHandler(Filters.text, get_preferences)
            ],

            BotStates.GET_SUBSCRIPTION_LENGTH: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), check_order),
                MessageHandler(Filters.text, get_subscription_length)
            ],

        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
        per_user=True,
        per_chat=True,
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()

    updater.idle()


class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        main()
