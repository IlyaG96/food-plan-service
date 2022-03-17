import json
import traceback

from django.core.management.base import BaseCommand
from tgbot.models import Allergy, Preference


def create_allergies(allergens):
    for allergen in allergens:
        current_allergen, created = Allergy.objects.get_or_create(
            title=allergen,
        )
        current_allergen.save()


def create_preferences(preferences):
    for preference in preferences:
        current_preference, created = Preference.objects.get_or_create(
            title=preference,
        )
        current_preference.save()


def add_to_db(path):
    with open(path, encoding='utf-8') as file:
        data = json.load(file)
        json.dumps(data)
        allergens = data['data']['allergens']
        preferences = data['data']['preferences']
        create_allergies(allergens)
        create_preferences(preferences)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path')

    def handle(self, *args, **options):
        path = options['path']
        if not path:
            path = 'json_examples/allergens_preferences.json'
        try:
            add_to_db(path)
        except FileNotFoundError:
            traceback.print_exc()
            print(f'\nФайл по пути {path} не найден')

