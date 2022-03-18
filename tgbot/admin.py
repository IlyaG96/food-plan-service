from django.contrib import admin
from .models import Dish, Product, Subscribe, User, Preference, Allergy, Bill
from django.db import models
from django.db.models.functions import Trunc
from django.db.models import Sum, Min, Max, DateTimeField

admin.site.register(Product)
admin.site.register(Preference)
admin.site.register(Allergy)
admin.site.register(Dish)


def get_next_in_date_hierarchy(request, date_hierarchy):
    if date_hierarchy + '__day' in request.GET:
        return 'hour'
    if date_hierarchy + '__month' in request.GET:
        return 'day'
    if date_hierarchy + '__year' in request.GET:
        return 'week'
    return 'month'


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    raw_id_fields = ('user', 'subscription')
    list_display = ['user', 'price', 'creation_date']
    list_filter = ['creation_date', 'subscription__sub_type']
    change_list_template = 'admin/bill_admin_change_list.html'
    date_hierarchy = 'creation_date'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_module_permission(self, request):
        return True

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
            'total': models.Count('subscription__sub_type'),
            'total_sales': models.Sum('price'),
        }
        response.context_data['summary'] = list(
            queryset
                .values('subscription__sub_type')
                .annotate(**metrics)
                .order_by('-total_sales')
        )

        response.context_data['summary_total'] = dict(
            queryset.aggregate(**metrics)
        )

        period = get_next_in_date_hierarchy(request, self.date_hierarchy)
        response.context_data['period'] = period

        summary_over_time = queryset.annotate(
                period=Trunc(
                    'creation_date',
                    'day',
                    output_field=DateTimeField(),
                ),
            ).values('period').annotate(total=Sum('price')).order_by('period')

        summary_range = summary_over_time.aggregate(
            low=Min('total'),
            high=Max('total')
        )

        high = summary_range.get('high', 0)
        low = summary_range.get('low', 0)
        response.context_data['summary_over_time'] = [{
            'period': x['period'],
            'total': x['total'] or 0,
            'percent': ((x['total'] or 0) - low) / (high - low) * 100 if high > low else 0,
        } for x in summary_over_time]
        print(response.context_data['summary_over_time'])

        return response

    class Meta:
        model = Bill
        fields = '__all__'


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
    readonly_fields = ('allowed_dishes', 'subscription_start')
    filter_horizontal = ('allergy',)
    fieldsets = (
        ('Общее', {
            'fields': [
                'subscriber',
                'preference',
                'allergy',
                'allowed_dishes',
                'subscription_start',
                'sub_type',
                'number_of_meals',
            ]
        }),
    )

    def allowed_dishes(self, obj):
        return ', \n'.join([dish.title for dish in obj.select_available_dishes()])

    allowed_dishes.short_description = 'Блюда, соответствующие условиям подписки'

    class Meta:
        model = Subscribe
