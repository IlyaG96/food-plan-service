from django.contrib import admin

from .models import Dish, Product, Subscribe, User, Preference, Allergy

admin.site.register(Product)
admin.site.register(Preference)
admin.site.register(Allergy)
admin.site.register(Dish)


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
class Subscribe(admin.ModelAdmin):
    raw_id_fields = ('subscriber', 'preference', 'allergy')
