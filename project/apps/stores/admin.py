from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin

from .models import Store


@admin.register(Store)
class StoreAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['__str__', 'domain', 'is_footer', 'is_active']
    list_filter = ['domain', 'is_footer', 'is_active']
    list_editable = ['is_footer', 'is_active']

