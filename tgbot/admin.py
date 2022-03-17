from django.contrib import admin

from .models import Dish, Product, Subscribe, User, Preference, Allergy
# Register your models here.

admin.site.register(Dish)
admin.site.register(Product)
admin.site.register(Preference)
admin.site.register(Allergy)


class SubscriptionAdmin(admin.StackedInline):
    model = Subscribe


@admin.register(User)
class User(admin.ModelAdmin):
    inlines = [
        SubscriptionAdmin
    ]

    class Meta:
        model = User


@admin.register(Subscribe)
class Image(admin.ModelAdmin):
    raw_id_fields = ('subscriber', 'preference')
