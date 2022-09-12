from django.contrib import admin
from django.db.utils import ProgrammingError
from .models import SberSettings, BankOrder


class SberSettingsAdmin(admin.ModelAdmin):
    # Создание объекта настроек по умолчанию
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # try
        # чтобы можно было выполнить создание миграций базы данных
        try:
            SberSettings.load().save()
        except ProgrammingError:
            pass

    def has_delete_permission(self, request, obj=None):
        return False


class BankOrderAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # try
        # чтобы можно было выполнить создание миграций базы данных
        try:
            SberSettings.load().save()
        except ProgrammingError:
            pass


admin.site.register(SberSettings, SberSettingsAdmin)
admin.site.register(BankOrder, BankOrderAdmin)
