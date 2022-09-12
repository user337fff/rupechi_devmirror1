from adminsortable2.admin import SortableAdminMixin
from apps.commons.admin import ImageModelAdmin
from apps.commons.admin import SingletonAdmin
from apps.template_editor.admin import TemplateAdminMixin
from apps.catalog.admin import CalcAdmin
from django import forms
from django.contrib import admin

from .models import Settings, IndexSlide, Delivery, Payment, CONTRACTOR_CHOICES, HTMLGroup, HTMLTag


@admin.register(Payment)
@admin.register(Delivery)
class BaseDeliveryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'get_domains']

    def get_domains(self, obj):
        if domains := obj.domain.all():
            return ', '.join([d.name for d in domains])
        return "Не выбрано"

    get_domains.short_description = 'Домены'
    get_domains.admin_order_field = 'domain'


class SettingsAdmin(TemplateAdminMixin, SingletonAdmin):
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Цветовая схема', {
            'fields': ('color_scheme',
                       'color_scheme_alpha',
                       'color_scheme_dark')
        }),
        ('Загружаемые логотипы', {
            'fields': ('logo', 'logo_email', 'favicon')
        }),
        ('Контактная информация', {

            'fields': (
                'address',
                'email',
                'phone',
                'extra_phones',
                ('lat', 'lon'),
                ('custom_field_title', 'custom_field_value'),
                'requisites'
            )
        }),
        ('Юридическая информация', {
            'fields': ('company_name', 'legal_address', 'domain')
        }),
        ('Социальные сети', {
            'fields': (
                'vkontakte',
                'facebook',
                'instagram',
                'telegram',
                'twitter',
                'youtube',
                'odnoklassniky',
            )
        }),

        ('Прочее', {
            'fields': (
                'banner_text',
                'banner_img',
                'card_payment',
                'card_shipping',
                'attr_chimney',
                'attr_second',
                'discount',
                'discount_domain',
                'type_price',
                'recipients',
            )
        }),
        ('SEO', {
            'fields': ['meta_title', 'meta_description', 'meta_keywords'],
        })
    )


@admin.register(IndexSlide)
class SliderAdmin(SortableAdminMixin, ImageModelAdmin, admin.ModelAdmin):
    list_display = ['__str__', 'get_image', 'get_domains']
    fieldsets = (
        (None, {
            'fields': ('domain', 'image', 'link',)
        }),
    )

    def get_domains(self, obj):
        if domains := obj.domain.all():
            return ', '.join([d.name for d in domains])
        return "Не выбрано"

    get_domains.short_description = 'Домены'
    get_domains.admin_order_field = 'domain'


class HTMLTagInline(admin.StackedInline):
    model = HTMLTag

class HTMLGroupAdmin(admin.ModelAdmin):
    model = HTMLGroup
    inlines = [HTMLTagInline]

admin.site.register(Settings, SettingsAdmin)
admin.site.register(HTMLGroup, HTMLGroupAdmin)