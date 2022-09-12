from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from simple_history.admin import SimpleHistoryAdmin

from apps.commons.admin import ExportExcelAdmin
from .forms import AccountCreationForm, AccountChangeForm
from .models import Account
from .export2xlsx import ExportLimiterAccount


class AccountAdmin(UserAdmin, SimpleHistoryAdmin, ExportExcelAdmin):
    add_form = AccountCreationForm
    form = AccountChangeForm
    change_list_template = "users/users_changelist.html"
    export_model = ExportLimiterAccount
    filter_horizontal = ('user_permissions',)
    model = Account

    list_display = (
        "email",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_active",
    )

    fieldsets = (
        (None, {"fields": ("name", "email", "phone", "password", 'contractor')}),
        (
            "Права доступа",
            {"fields": ("is_staff", "is_active", "is_superuser",
                        "groups", "user_permissions")},
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active"),
            },
        ),
    )
    readonly_fields = [
        "last_login",
        "date_joined",
    ]
    search_fields = ("email",)
    ordering = ("email",)

    def get_form(self, request, obj=None, **kwargs):
        """
        Ограничение возможности пользователей к редактированию своего профиля
        """
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser

        disabled_fields: set = set()
        if not is_superuser:
            disabled_fields |= {
                "is_superuser",
            }

            if obj is not None:
                disabled_fields |= {"email"}

        if not is_superuser and obj is not None and obj == request.user:
            disabled_fields |= {
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            }

        for f in disabled_fields:
            if f in form.base_fields:
                form.base_fields[f].disabled = True
        return form

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.has_perm("users.delete_account"):
            del actions["delete_selected"]
        return actions


admin.site.register(Account, AccountAdmin)
