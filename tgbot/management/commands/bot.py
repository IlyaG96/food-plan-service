from django.core.management.base import BaseCommand
from django.conf import settings
from tgbot.bot_modules.main import main

class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        main()
