from django.db import models


class Preference(models.Model):
    title = models.CharField('Предпочтения', max_length=200)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Предпочтение'
        verbose_name_plural = 'Предпочтения'


class Allergy(models.Model):
    title = models.CharField('Аллергия', max_length=200)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Аллергия'
        verbose_name_plural = 'Аллергии'


class User(models.Model):
    first_name = models.CharField('Имя', max_length=250)
    last_name = models.CharField('Фамилия', max_length=250, blank=True)
    chat_id = models.IntegerField('Chat id', unique=True)
    phone = models.CharField('Номер телефона', max_length=20, blank=True)

    def __str__(self):
        return f'ID: {self.chat_id} имя: {self.first_name} телефон: {self.phone}'

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'


class Product(models.Model):
    title = models.CharField('Название продукта', max_length=200)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Dish(models.Model):
    title = models.CharField('Название блюда', max_length=200)
    description = models.TextField('Описание Блюда')
    cooking_method = models.TextField('Способ приготовления')
    image = models.ImageField(
        "Изображение",
        null=True,
        blank=True,
    )
    ingredients = models.ManyToManyField(
        Product,
        verbose_name='Ингридиенты',
        related_name='dishes',
    )
    preferences = models.ForeignKey(
        Preference,
        verbose_name='Подходит для:',
        related_name='appropriate_dishes',
        on_delete=models.SET_NULL,
        null=True,
    )
    allergy = models.ManyToManyField(
        Allergy,
        verbose_name='Не подходит для:',
        related_name='inappropriate_dishes',
    )
    calories = models.PositiveSmallIntegerField(
        'Калорийность',
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.title}'

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'


class Subscribe(models.Model):
    title = models.CharField('Название', max_length=200)
    subscriber = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        related_name='subscribes',
        on_delete=models.CASCADE,
    )
    preference = models.ForeignKey(
        Preference,
        verbose_name='Предпочтения',
        related_name='subscribes',
        on_delete=models.CASCADE,
    )
    allergy = models.ManyToManyField(
        Allergy,
        verbose_name='Аллергии',
        related_name='subscribes',
        blank=True
    )
    number_of_meals = models.PositiveSmallIntegerField(
        'Количество приемов пищи в день',
    )
    subscription_period = models.DateField(
        'Срок действия подписки',
        blank=True,
        null=True,
    )
    dish = models.ManyToManyField(
        Dish,
        verbose_name='Блюда',
        related_name='dishes'
    )

    def __str__(self):
        return f'Подписка {self.pk} - {self.title} - {self.subscriber.first_name}'

    def select_available_dishes(self):
        allergens = [allergy for allergy in self.allergy.all()]
        preference = self.preference
        dishes = Dish.objects.filter(preferences=preference).exclude(allergy__in=allergens)
        self.dishes = dishes

        return self.dishes


class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
