from django.contrib import admin
from django.db.utils import ProgrammingError
from django.urls import reverse
from .models import KomtetSettings


class KomtetSettingsAdmin(admin.ModelAdmin):

    change_form_template = 'admin/komtet/change_form.html'

    # Создание объекта настроек по умолчанию
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # try
        # чтобы можно было выполнить создание миграций базы данных
        try:
            KomtetSettings.load().save()
        except ProgrammingError:
            pass

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(KomtetSettings, KomtetSettingsAdmin)
