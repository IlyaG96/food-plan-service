from django.contrib import admin

from .models import Dish, Product, Subscribe, User, Preference, Allergy
# Register your models here.

admin.site.register(Dish)
admin.site.register(Product)
admin.site.register(Subscribe)
admin.site.register(User)
admin.site.register(Preference)
admin.site.register(Allergy)
