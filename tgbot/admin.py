from django.contrib import admin
from .models import Dish, Product, Subscribe, User, Preference, Allergy, Bill

admin.site.register(Product)
admin.site.register(Preference)
admin.site.register(Allergy)
admin.site.register(Dish)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):

    raw_id_fields = ('user', 'subscription')
    list_display = ['user', 'subscription_length', 'price', 'creation_date', 'total_amount']

    def subscription_length(self, obj):
        return obj.subscription.subscription_period

    subscription_length.short_description = 'Конец подписки'
    # TODO use annotate in QuerySet

    def total_amount(self, obj):

        bills = Bill.objects.all()
        total_amount = sum([bill.price for bill in bills])
        return total_amount

    total_amount.short_description = 'Общая сумма'


    class Meta:
        model = Bill


class SubscriptionAdmin(admin.StackedInline):
    model = Subscribe


@admin.register(User)
class User(admin.ModelAdmin):
    inlines = [
        SubscriptionAdmin
    ]
    filter_horizontal = ('favorite_dishes', 'unloved_dishes')

    class Meta:
        model = User


@admin.register(Subscribe)
class Subscribe(admin.ModelAdmin):
    raw_id_fields = ('subscriber', 'preference', 'allergy')
    readonly_fields = ('allowed_dishes',)
    filter_horizontal = ('allergy',)
    fieldsets = (
        ('Общее', {
            'fields': [
                'subscriber',
                'preference',
                'allergy',
                'allowed_dishes',
                'subscription_period',
            ]
        }),
    )

    def allowed_dishes(self, obj):
        return ", ".join([dish.title for dish in obj.select_available_dishes()])

    allowed_dishes.short_description = 'Блюда, соответствующие условиям подписки'

    class Meta:
        model = Subscribe
