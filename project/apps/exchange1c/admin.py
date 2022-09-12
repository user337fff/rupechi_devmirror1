from django.contrib import admin
from django.db.utils import ProgrammingError
from .models import Settings


class SettingsAdmin(admin.ModelAdmin):
    readonly_fields = ['last_export_date']

    fieldsets = (
        ('Обмен заказами', {
            'fields': ('orders_from_1c', 'order_prefix', 'only_paid_orders',
                       'only_allowed_delivery_orders', 'change_statuses_from_1c', 'orders_status_gte',
                       'delivery_for_new')
        }),
        ('Экспорт физических лиц', {
            'fields': ('full_name', 'name', 'last_name',
                       'address', 'postcode', 'city',
                       'street', 'email')
        }),
        ('Экспорт юридических лиц', {
            'fields': ('full_name_ur', 'inn_ur', 'kpp_ur',
                       'address_ur', 'country_ur', 'city_ur',
                       'street_ur', 'phone_ur', 'email_ur')
        }),
        ('Отображение товаров в каталоге', {
            'fields': ('know_price_instead_add_cart_button',
                       'notify_instead_add_cart_button',
                       'hide_not_in_stock')
        }),
        ('Другое', {
            'fields': ('variation_grouping', 'last_export_date')
        }),
    )

    # Создание объекта настроек по умолчанию
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # try
        # чтобы можно было выполнить создание миграций базы данных
        try:
            Settings.load().save()
        except ProgrammingError:
            pass

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Settings, SettingsAdmin)
