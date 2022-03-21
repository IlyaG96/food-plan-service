import pathlib
from enum import Enum
from django.conf import settings
from django.utils import timezone
from random import choices
from telegram import (
    LabeledPrice,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)
from telegram.ext import (CallbackQueryHandler,
                          CommandHandler,
                          ConversationHandler,
                          PreCheckoutQueryHandler,
                          Filters,
                          MessageHandler,
                          Updater,)
from tgbot.models import User, Allergy, Preference, Bill, Subscribe, Dish
from telegram.error import BadRequest
from textwrap import dedent
from django.db.models import Count

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
    HANDLE_DISH = 15


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
    user_id = update.message.chat_id
    context.user_data['user_id'] = user_id
    if not User.objects.filter(chat_id__contains=user_id):
        return get_username(update, context)
    keyboard = [['Мои подписки', 'Новая подписка']]
    update.message.reply_text('Привет! '
                              'Я - бот, который составит для тебя рацион питания и упростит жизнь. '
                              'Хочешь посмотреть свои подписки или создать новую?',
                              reply_markup=ReplyKeyboardMarkup(keyboard=keyboard,
                                                               resize_keyboard=True))

    return BotStates.GREET_USER


def get_username(update, context):
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


def add_new_user(update, context):
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
    first_name, last_name = context.user_data['username'].split(' ')
    chat_id = context.user_data['user_id']
    User.objects.get_or_create(
        first_name=first_name,
        last_name=last_name,
        chat_id=chat_id,
        phone=phone,
    )
    return start(update, context)


def get_portion_size(update, context):
    # if update.message.text != 'Назад ⬅':

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
    preferences = Preference.objects.all()
    keyboard = build_menu([preference.title for preference in preferences],
                          n_cols=2,
                          footer_buttons=['Назад ⬅'])
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
        'Пометь крестиком \U0000274C те продукты, на которые у тебя аллергия. Как только закончишь, нажимай "Готово", '
        'Если аллергии нет, можно нажать "Пропустить"',
        reply_markup=ReplyKeyboardMarkup(keyboard=[['Пропустить', 'Готово']],
                                         resize_keyboard=True,
                                         ),
    )

    allergens = Allergy.objects.all()
    context.user_data['allergens'] = [
        allergen.title + ' \U0001F7E2' for allergen in allergens]
    allergens = context.user_data['allergens']

    context.bot.send_message(
        text='У меня аллергия на:',
        chat_id=context.user_data['user_id'],
        reply_markup=InlineKeyboardMarkup(build_menu(
            ([InlineKeyboardButton(allergen,
                                   callback_data=allergen)
              for allergen in allergens]),
            n_cols=1))
    )

    return BotStates.HANDLE_ALLERGY


def handle_allergy(update, context):
    allergens = context.user_data['allergens']
    callback_query = update.callback_query
    choice = callback_query.data
    if choice in allergens and '\U0000274C' in choice:
        allergen_index = allergens.index(choice)
        allergens[allergen_index] = choice.replace('\U0000274C', '\U0001F7E2')
    if choice in allergens:
        allergen_index = allergens.index(choice)
        allergens[allergen_index] = choice.replace('\U0001F7E2', '\U0000274C')

    context.bot.edit_message_text(
        text='У меня аллергия на:',
        message_id=callback_query.message.message_id,
        chat_id=context.user_data['user_id'],
        reply_markup=InlineKeyboardMarkup(build_menu(
            ([InlineKeyboardButton(allergen,
                                   callback_data=allergen)
              for allergen in allergens]),
            n_cols=1))
    )


def get_portions_quantity(update, context):
    if update.message.text == 'Пропустить':
        context.user_data['allergens'] = None
    # TODO replace from db
    keyboard = build_menu([str(num) for num in range(1, 7)],
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

    user = User.objects.get(chat_id=context.user_data['user_id'])
    username = ' '.join([user.first_name, user.last_name])
    phonenumber = user.phone
    portions_quantity = context.user_data['portions_quantity']
    portion_size = context.user_data['portion_size']
    allergens = context.user_data['allergens']
    preferences = context.user_data['preferences']
    subscription_length = context.user_data['subscription_length']

    price = int(portions_quantity) * int(portion_size) * int(subscription_length)
    # in test payment price should be less than 1000 rub!
    context.user_data['price'] = price

    preference = Preference.objects.get(title=preferences)
    subscription, created = Subscribe.objects.get_or_create(
        title='Подписка',
        subscriber=user,
        preference=preference,
        number_of_meals=portions_quantity,
        persons_quantity=portion_size,
        sub_type=subscription_length,
        subscription_start=timezone.now(),
    )

    if allergens:
        allergens = list(filter(lambda word: '\U0000274C' in word, allergens))
        for allergen in allergens:
            allergen = allergen.split(' \U0000274C')[0]
            subscription.allergy.add(
                Allergy.objects.get(title=allergen)
            )

    order = dedent(
        f'''
    Имя: {username}
    Номер телефона: {phonenumber}
    Количество приемов пищи в день: {portions_quantity}
    Размер блюда рассчитан на: {portion_size} человек
    Предпочтения: {preferences}
    Исключения из рациона: {allergens}
    Длительность подписки: {subscription_length} месяца
    Общая стоимость: {price} руб.
    Тестовая оплата ЮКАССЫ должна быть менее 1000 рублей!
    ''')

    # TODO must be in done() function on production

    user = User.objects.get(chat_id=context.user_data['user_id'])
    bill = Bill.objects.create(
        user=user,
        subscription=subscription,
        creation_date=timezone.now(),
        price=context.user_data['price'],
    )
    bill.save()

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
    prices = [LabeledPrice('Стоимость', price * 100)]

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )

    return BotStates.PRECHECKOUT


def precheckout(update, _):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        query.answer(ok=False, error_message='Что-то пошло не так...')
    else:
        query.answer(ok=True)

    return BotStates.SUCCESS_PAYMENT


def done(update, context):
    update.message.reply_text(
        'До свидания!',
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def send_notification(context):
    users = User.objects.all().prefetch_related('subscribes')

    for user in users:
        for subscribe in user.subscribes.all():
            number_of_meals = subscribe.number_of_meals
            end_sub_date = subscribe.subscription_start + timezone.timedelta(days=int(subscribe.sub_type) * 30)
            if end_sub_date > timezone.now().date():
                available_dishes = choices([dish for dish in Subscribe.select_available_dishes(subscribe)],
                                           k=number_of_meals)
                try:
                    context.bot.send_message(
                        chat_id=user.chat_id,
                        text='Время кормить себя! Кажется, в соответствии с вашей подпиской, вы можете себе '
                             'позволить: ',
                        reply_markup=InlineKeyboardMarkup
                        (inline_keyboard=[([InlineKeyboardButton(dish.title,
                                                                 callback_data=f'{dish.id} reg')]) for dish in
                                          available_dishes])
                    )

                except BadRequest as e:
                    pass


def get_dishes_to_show(subscribe_id):
    subscribe = Subscribe.objects.annotate(all_shown_dishes=Count('shown_dishes')).get(id=subscribe_id)
    days_gone = timezone.now().date() - subscribe.subscription_start
    number_of_meals = subscribe.number_of_meals
    dishes_shown = number_of_meals * days_gone.days
    if subscribe.all_shown_dishes < dishes_shown:
        available_dishes = Subscribe.select_available_dishes(subscribe)
        for dish in available_dishes.all()[:dishes_shown]:
            subscribe.shown_dishes.add(dish)
    dishes_shown_id = [dish_shown.id for dish_shown in subscribe.shown_dishes.all()]
    dishes_to_show = Subscribe.select_available_dishes(subscribe) \
                              .exclude(id__in=dishes_shown_id)
    return dishes_to_show.prefetch_related('ingredients')[:number_of_meals]


def send_dish(update, context):
    callback_query = update.callback_query
    subscribe_id = callback_query.data
    
    dishes = get_dishes_to_show(subscribe_id)
    for dish in dishes:
        dish_ingredients = ''.join(
            [ingredient.title for ingredient in dish.ingredients.all()]
        )
        picture = dish.image.url
        path = pathlib.Path().resolve()
        photo_path = str(path) + str(picture)
        context.bot.send_photo(
            photo=open(file=photo_path, mode='rb'),
            chat_id=callback_query.message.chat.id,
            reply_markup='',

            caption=dedent(f'''
            Для приготовления блюда "{dish.title}" вам понадобятся:
            {dish_ingredients}        
            ''')
        )
    #    context.bot.send_message(
    #        text=dedent(f'''
    #        Способ приготовления:
    #        {dish.cooking_method}
    #        '''
    #                    ),
    #        chat_id=callback_query.message.chat.id,
    #    )


def calculate_end_sub_date(subscribe):
    sub_type = subscribe.sub_type
    subscription_start = subscribe.subscription_start
    return subscription_start + timezone.timedelta(days=int(sub_type) * 30)


def handle_subscriptions(update, context):
    user_id = context.user_data['user_id']
    user = User.objects.get(chat_id=user_id)

    for subscribe in user.subscribes.all():
        allergies = ', '.join([allergy.title for allergy in subscribe.allergy.all()])
        end_sub_date = calculate_end_sub_date(subscribe)
        # TODO use 'continue' button only on subs that near to end_sub, not on active
        if end_sub_date > timezone.now().date():
            subscription = dedent(
                f'''
            {subscribe.title} от {subscribe.subscription_start}\n
            Заканчивается: {end_sub_date}
            Предпочтения: {subscribe.preference}
            Непереносимость продуктов: {allergies}
            Количество приемов пищи в день: {subscribe.number_of_meals} приема
            Количество человек: {subscribe.persons_quantity} человек
            Подписка на: {subscribe.sub_type} месяцев
            ''')

            context.bot.send_message(
                text=subscription,
                chat_id=user_id,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton('Хочу есть!',
                                              callback_data=f'{subscribe.id}')]
                    ],
                ),
            )

    return BotStates.GREET_USER


def main():
    updater = Updater(settings.TGBOT_TOKEN)
    dispatcher = updater.dispatcher
    # job_queue = dispatcher.job_queue
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BotStates.GREET_USER: [
                CallbackQueryHandler(send_dish, pattern='[0-9]{1,10}$'),
                MessageHandler(Filters.regex(r'Мои подписки$'), handle_subscriptions),
                MessageHandler(Filters.regex(r'Новая подписка$'), get_portion_size),
                # MessageHandler(Filters.text, get_username)
            ],
            BotStates.GET_USERNAME: [
                MessageHandler(Filters.regex(r'[а-яА-Яa-zA-Z]{2,20}( )[а-яА-Яa-zA-Z]{2,20}$'),
                               get_user_phonenumber),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), start),
                MessageHandler(Filters.text, get_username)
            ],

            BotStates.GET_PHONENUMBER: [
                MessageHandler(Filters.contact, add_new_user),
                MessageHandler(Filters.regex(r'^\+?\d{1,3}?( |-)?\d{3}( |-)?\d{3}( |-)?\d{2}( |-)?\d{2}$'),
                               add_new_user),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), get_username),
                # MessageHandler(Filters.text, get_user_phonenumber)
            ],

            BotStates.GET_PORTIONS_SIZE: [
                MessageHandler(Filters.regex(r'[0-9]{1,2}$'), get_preferences),
                MessageHandler(Filters.regex(r'^Назад ⬅$'), start),
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
                CallbackQueryHandler(handle_allergy, pattern='[а-яА-Я\U0000274C\U0001F7E2 ]{2,30}$'),
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
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
        per_user=True,
        per_chat=False,
        allow_reentry=True
    )
    # dispatcher.add_handler(CallbackQueryHandler(send_dish, pattern='[0-9 reg]{1,10}$'))  # TODO fix this

    dispatcher.add_handler(conv_handler)
    # job_queue.set_dispatcher(dispatcher)
    # job_queue.run_repeating(callback=send_notification, interval=settings.BOT_DELAY, first=7200.0)

    updater.start_polling()

    updater.idle()
