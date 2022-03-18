from django.contrib import admin
from .models import Dish, Product, Subscribe, User, Preference, Allergy, Bill
from django.db import models

admin.site.register(Product)
admin.site.register(Preference)
admin.site.register(Allergy)
admin.site.register(Dish)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):

    raw_id_fields = ('user', 'subscription')
    list_display = ['user', 'subscription_length', 'price', 'creation_date']
    list_filter = ['creation_date']
    change_list_template = 'admin/bill_admin_change_list.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        try:
            queryset = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        metrics = {
            'total': models.Count('id'),
            'total_sales': models.Sum('price'),
        }
        response.context_data['summary'] = list(
            queryset
                .values('subscription')
                .annotate(**metrics)
                .order_by('-total_sales')
        )

        response.context_data['summary_total'] = dict(
            queryset.aggregate(**metrics)
        )

        return response



    def subscription_length(self, obj):
        return obj.subscription.subscription_period

    subscription_length.short_description = 'Конец подписки'

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
