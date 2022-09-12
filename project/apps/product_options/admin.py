from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin

from . import models as option_models


class OptionValueInline(SortableInlineAdminMixin, admin.TabularInline):
    model = option_models.OptionValue
    extra = 1


class OptionAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    inlines = (OptionValueInline,)


admin.site.register(option_models.Option, OptionAdmin)
admin.site.register(option_models.OptionValue)
admin.site.register(option_models.ProductOption)
