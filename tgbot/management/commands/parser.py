import random
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from tgbot.models import Dish, Product, Allergy, Preference


def upload_image(image_url, title):
    dish = Dish.objects.get(title=title)
    name = urlparse(image_url).path.split('/')[-1]
    url = urljoin('https:', image_url)

    image_response = requests.get(url)
    image_response.raise_for_status()
    image_content = ContentFile(image_response.content)

    dish.image.save(
        name,
        image_content,
        save=True
    )


def get_recipe(url):
    dish_page_response = requests.get(url)
    dish_page_response.raise_for_status()
    dish_page = dish_page_response.text

    dish_page_soup = BeautifulSoup(dish_page, 'lxml')
    title = dish_page_soup.select_one('h1.title')
    title = title.text

    description = dish_page_soup.select_one('.recipe_new tr td div p')
    description = description.text

    cooksteps_text = []
    cook_steps = dish_page_soup.select('.step_images_n')
    for step in cook_steps:
        step_text = step.text.strip()
        cooksteps_text.append(step_text)

    preferences = Preference.objects.all()
    rand_preference = random.choice(preferences)

    dish, created = Dish.objects.get_or_create(
        title=title,
        defaults={
            'description': description,
            'cooking_method': cooksteps_text,
            'preferences': rand_preference,
        }
    )

    picture = dish_page_soup.select_one('a.tozoom')
    image_url = picture.get('href')

    upload_image(image_url, title)

    ingredients = []
    products = dish_page_soup.select('.ingr_tr_0')
    for product in products:
        product = product.text
        formatted_product = product.split(' – ')[0].split(' - ')
        prod, created = Product.objects.get_or_create(
            title=formatted_product[0])
        dish.ingredients.add(prod)
        ingredients.append(product)

    allergies = Allergy.objects.all()
    allergies_number = random.randint(0, len(allergies)-2)
    if allergies_number:
        rand_allergies = random.sample(list(allergies), allergies_number)
        for allergy in rand_allergies:
            dish.allergy.add(allergy)

    print(f'Добавлено блюдо: "{title}"')


def get_recipe_urls(url):
    page_number = 1

    params = {
        'page': page_number,
    }

    recipes_response = requests.get(url)
    recipes_response.raise_for_status()

    urls_page_soup = BeautifulSoup(recipes_response.text, 'lxml')
    urls = urls_page_soup.select('.title a')
    print(urls)
    urls_list = []
    for url in urls:
        url = url.get('href')
        urls_list.append(url)

    return urls_list


def main():
    start_page = 'https://www.russianfood.com/recipes/bytype/?fid=3'
    default_url = 'https://www.russianfood.com'
    urls_list = get_recipe_urls(start_page)

    for url in urls_list:
        url = urljoin(default_url, url)
        get_recipe(url)


class Command(BaseCommand):
    help = 'Парсер блюд'

    def handle(self, *args, **options):
        main()
