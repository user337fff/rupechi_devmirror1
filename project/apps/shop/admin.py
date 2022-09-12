from django.contrib import admin
from django.db.models import Sum

from apps.commons.admin import ExportExcelAdmin
from .export2xlsx import ExportLimiterOrder
from .models import Order, OrderItem, EndPoint


class OrderItemInline(admin.TabularInline):
    model = OrderItem


@admin.register(EndPoint)
class EndPointAdmin(admin.ModelAdmin):
    list_display = ['slug', 'store', 'domain']


class OrderAdmin(ExportExcelAdmin):
    list_display = ("__str__", "status", "paid", "name", "phone",
                    "email", "total", "created_at")
    list_filter = ("status", "paid")
    search_fields = ("name", "user__name", "user__email")
    inlines = [OrderItemInline]
    readonly_fields = ("bonuses_used", "paid", "status_export")
    date_hierarchy = "created_at"

    export_model = ExportLimiterOrder
    change_list_template = "shop/orders_changelist.html"

    actions = ["sum_orders", ]

    def sum_orders(self, request, queryset):
        price_sum = queryset.aggregate(price_sum=Sum("total")).get("price_sum", 0)
        message = u"Сумма заказов: %s руб." % price_sum
        ids = queryset.values_list("id", flat=True)
        message += u" Заказы №%s" % ", ".join(str(item) for item in ids)
        message += u" Число заказов: %s" % len(ids)
        self.message_user(request,  message)

    sum_orders.short_description = u"Сумма заказов"

    def save_model(self, request, obj, form, change):
        """ Добавление бонусов из панели администратора """
        if not obj.pk:
            super().save_model(request, obj, form, change)
            obj._created()
        else:
            super().save_model(request, obj, form, change)


admin.site.register(Order, OrderAdmin)
