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
    GET_ALLERGY = 6
    HANDLE_ALLERGY = 7
    GET_PORTIONS_QUANTITY = 8
    GET_SUBSCRIPTION_LENGTH = 9
    CHECK_ORDER = 10
    TAKE_PAYMENT = 11
    PRECHECKOUT = 12
    SUCCESS_PAYMENT = 13
    HANDLE_SUBSCRIPTIONS = 14


def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def start(update, context):
    keyboard = [['Мои подписки', 'Новая подписка']]
    update.message.reply_text('Привет! '
                              'Я - бот, который составит для тебя рацион питания и упростит жизнь. '
                              'Хочешь посмотреть свои подписки или создать новую?',
                              reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                                               resize_keyboard=True))

    return BotStates.GREET_USER


def get_username(update, context):
    # TODO pass if user exists
    user_id = update.message.chat_id
    context.user_data['user_id'] = user_id

    keyboard = [['Передать контакт (не жмякать, не работает)']]
    update.message.reply_text(
        'Познакомимся? Пожалуйста, представься. Напиши имя и фамилию',
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         input_field_placeholder='Иван Иванов',
                                         ))

    return BotStates.GET_USERNAME


def get_user_phonenumber(update, context):
    if update.message.text != 'Назад ⬅':
        context.user_data['username'] = update.message.text

    phone_request_button = KeyboardButton('Передать контакт',
                                          request_contact=True)

    keyboard = [[phone_request_button, 'Назад ⬅']]
    update.message.reply_text(
        'Мне понадобится номер телефона. Можно отправить свой номер из профиля или ввести вручную',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard,
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
    keyboard = build_menu([str(num) for num in range(1, 11)],
                          n_cols=5,
                          footer_buttons=['Назад ⬅'])
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

    keyboard = build_menu(['Мясоед',
                           'Предпочитаю рыбов',
                           'Убежденный веган',
                           'Всего и побольше',
                           'Низкокалорийная диета',
                           ], n_cols=2,
                          footer_buttons=['Назад ⬅']
                          )
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


def get_allergy(update, context):
    if update.message.text != 'Назад ⬅':
        preferences = update.message.text
        context.user_data['preferences'] = preferences

    update.message.reply_text(
        'Выбери продукты, на которые у тебя аллергия. Как только закончишь, нажимай "Готово", '
        'Если аллергии нет, можно нажать "Пропустить"',
        reply_markup=ReplyKeyboardMarkup(keyboard=[['Пропустить', 'Готово']],
                                         resize_keyboard=True,
                                         ),
    )
    context.user_data['allergens'] = ['Рыба и морепродукты',
                                      'Мясо',
                                      'Зерновые',
                                      'Продукты пчеловодства',
                                      'Орехи и бобовые',
                                      'Молочные продукты']

    allergens = context.user_data['allergens']

    context.bot.send_message(
        text='У меня аллергия на:',
        chat_id=context.user_data['user_id'],
        reply_markup=InlineKeyboardMarkup(build_menu(
            ([InlineKeyboardButton(allergen,
                                   callback_data=allergen)
              for allergen in allergens]),
            n_cols=2))
    )

    return BotStates.HANDLE_ALLERGY


def handle_allergy(update, context):
    allergens = context.user_data['allergens']

    callback_query = update.callback_query
    choice = callback_query.data
    if choice in allergens and '*' in choice:
        allergen_index = allergens.index(choice)
        allergens[allergen_index] = choice.replace('*', "")
    if choice in allergens:
        allergen_index = allergens.index(choice)
        allergens[allergen_index] = choice + '*'


    context.bot.edit_message_text(
        text='У меня аллергия на:',
        message_id=callback_query.message.message_id,
        chat_id=context.user_data['user_id'],
        reply_markup=InlineKeyboardMarkup(build_menu(
            ([InlineKeyboardButton(allergen,
                                   callback_data=allergen)
              for allergen in allergens]),
            n_cols=2))
    )


def get_portions_quantity(update, context):
    # TODO replace from db
    keyboard = build_menu([str(num) for num in range(1, 11)],
                          n_cols=5,
                          footer_buttons=['Назад ⬅'])
    update.message.reply_text(
        'Сколько приемов пищи в день планируется?',
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
    keyboard = build_menu(['1', '3', '6', '9', '12'], n_cols=3, footer_buttons=['Назад ⬅'])
    update.message.reply_text(
        'На сколько месяцев оформить подписку?',
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
    allergens = list(filter(lambda word: '*' in word, context.user_data['allergens']))
    preferences = context.user_data['preferences']
    subscription_length = context.user_data['subscription_length']
    price = int(portions_quantity) * int(portion_size) * int(subscription_length)
    # in test payment price should be less than 1000 rub!
    context.user_data['price'] = price

    # TODO get price from DB
    order = dedent(
        f'''
    Имя: {username}
    Номер телефона: {phonenumber}
    Количество приемов пищи в день: {portions_quantity}
    Размер блюда рассчитан на: {portion_size} человек
    Предпочтения: {preferences}
    Аллергия: {allergens}
    Длительность подписки: {subscription_length}
    Общая стоимость: {price} руб.
    Тестовая оплата ЮКАССЫ должна быть менее 1000 рублей!
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
    description = f'Оплата заказа стоимостью {price} рублей'
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


def handle_subscriptions(update, context):
    keyboard = [['Назад ⬅']]
    text = dedent(
        # subscriptions from User.subscriptions.all()
        'Тут пока пусто, приходи позже :)'
    )
    update.message.reply_text(text=text,
                              reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                                               resize_keyboard=True))

    return BotStates.HANDLE_SUBSCRIPTIONS


def main():
    updater = Updater(settings.TGBOT_TOKEN)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', get_username)],
        states={
            BotStates.GREET_USER: [
                MessageHandler(Filters.regex(r'Мои подписки$'), handle_subscriptions),
                MessageHandler(Filters.regex(r'Новая подписка$'), get_username),
                MessageHandler(Filters.text, get_username)
            ],
            BotStates.GET_USERNAME: [
                MessageHandler(Filters.regex(r'[а-яА-Яa-zA-Z]{2,20}( )[а-яА-Яa-zA-Z]{2,20}$'),
                               get_user_phonenumber),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), start),
                MessageHandler(Filters.text, get_username)
            ],

            BotStates.GET_PHONENUMBER: [
                MessageHandler(Filters.contact, get_portion_size),
                MessageHandler(Filters.regex(r'^\+?\d{1,3}?( |-)?\d{3}( |-)?\d{3}( |-)?\d{2}( |-)?\d{2}$'),
                               get_portion_size),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_username),
                MessageHandler(Filters.text, get_user_phonenumber)
            ],

            BotStates.GET_PORTIONS_SIZE: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), get_preferences),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_user_phonenumber),
                MessageHandler(Filters.text, get_portion_size)
            ],

            BotStates.GET_PREFERENCES: [
                MessageHandler(Filters.regex(r'[а-яА-Я ]{2,30}$'), get_allergy),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_portion_size),
                MessageHandler(Filters.text, get_preferences)
            ],
            BotStates.GET_ALLERGY: [
                MessageHandler(Filters.regex(r'[а-яА-Я ]{2,20}$'), get_portions_quantity),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_preferences),
                MessageHandler(Filters.regex(r'^Пропустить$'), get_subscription_length),
                MessageHandler(Filters.text, get_allergy)
            ],
            BotStates.HANDLE_ALLERGY: [
                CallbackQueryHandler(handle_allergy, pattern='[а-яА-Я* ]{2,30}$'),
                CallbackQueryHandler(get_portions_quantity, pattern='^Готово$'),
                MessageHandler(Filters.regex(r'^Пропустить$'), get_portions_quantity),
                MessageHandler(Filters.regex(r'^Готово'), get_portions_quantity),
            ],
            BotStates.GET_PORTIONS_QUANTITY: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), get_subscription_length),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_allergy),
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
            BotStates.HANDLE_SUBSCRIPTIONS: [
                MessageHandler(Filters.regex(r'^Назад ⬅$'), start),
                MessageHandler(Filters.text, start)
            ]

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
