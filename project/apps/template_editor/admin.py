from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.conf import settings
from .models import TemplateModel
from .forms import TemplateForm
from .finder import template_list
from .views import TemplateEditFormView, get_template_content


class TemplateAdminMixin(admin.ModelAdmin):
    """
    Данный класс добавляет редактор шаблонов
    Из-за особенностей админки может быть выведен только с моделью
    """
    change_list_template = "template_editor/admin/changelist_with_template_editor.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('edit_template/', TemplateEditFormView.as_view()),
            path('template_content/', self.admin_site.admin_view(get_template_content)),
        ]
        return my_urls + urls




# admin.site.register(TemplateModel, TemplateAdmin)