from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    message
)
from telegram.ext import (CallbackContext, CallbackQueryHandler, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)


def start(update, context):
    update.message.reply_text('Привет!')
    
    return


def done(update, context):
    """End conversation."""

    update.message.reply_text(
        'До свидания!',
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.TGBOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # TODO
        },
        fallbacks=[MessageHandler(Filters.regex('^Выход$'), done)],
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        main()
      