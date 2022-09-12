from django.contrib import admin
from django import forms
from django.utils import timezone
from django.db.utils import ProgrammingError
from django.contrib.admin.utils import flatten_fieldsets

from .models import BonusSettings, BonusCategory, BonusAccount, Action


class BonusSettingsAdmin(admin.ModelAdmin):
    # Создание объекта настроек по умолчанию
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        # try
        # чтобы можно было выполнить создание миграций базы данных
        try:
            BonusSettings.load().save()
        except ProgrammingError:
            pass

    def has_delete_permission(self, request, obj=None):
        return False


class BonusAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'updated_at', 'created_at')
    readonly_fields = ('balance', 'updated_at', 'created_at')

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        """ Добавление бонусов из панели администратора """
        if not obj.pk:
            BonusAccount.create(obj.user, timezone.now())
        else:
            super().save_model(request, obj, form, change)


class ActionAdminForm(forms.ModelForm):
    """
    Форма для заполнения через панель администратора
    тип "Создание аккаунта" вырезан
    убраны дата создания и остаток на балансе
    """
    type = forms.ChoiceField(choices=Action.TYPE_CHOICES[1:])

    class Meta:
        model = Action
        exclude = ('created_at', 'debug_balance')


class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'account',
        'order',
        'delta',
        'type',
        'expires_at',
        'debug_balance')

    list_filter = ('account',)
    form = ActionAdminForm

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(ActionAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def save_model(self, request, obj, form, change):
        """ Добавление бонусов из панели администратора """
        if not obj.pk:
            if obj.type == obj.TYPE_DEPOSITED:
                BonusAccount.deposit(
                    obj.account.pk,
                    abs(obj.delta),
                    timezone.now(),
                    expires_at=obj.expires_at,
                    comment=obj.comment)
            elif obj.type == obj.TYPE_WITHDRAWN:
                BonusAccount.withdraw(
                    obj.account.pk,
                    obj.delta,
                    timezone.now(),
                    comment=obj.comment)
        else:
            super().save_model(request, obj, form, change)


admin.site.register(BonusSettings, BonusSettingsAdmin)
admin.site.register(BonusCategory)
admin.site.register(BonusAccount, BonusAccountAdmin)
admin.site.register(Action, ActionAdmin)
