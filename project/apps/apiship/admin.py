from django.contrib import admin

from .models import Settings, OrderShipping

from django.db.utils import ProgrammingError


class SettingsAdmin(admin.ModelAdmin):
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
admin.site.register(OrderShipping)
