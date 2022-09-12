from django.contrib import admin

from .models import Domain, SeoContentFromLinks
from ..seo.admin import SeoAdminMixin


class SeoContentFromLinksAdmin(admin.TabularInline):
    model = SeoContentFromLinks

@admin.register(Domain)
class DomainAdmin(SeoAdminMixin, admin.ModelAdmin):
    list_display = ('domain', 'name')
    search_fields = ('domain', 'name')

    inlines = [
        SeoContentFromLinksAdmin,
    ]

    fieldsets = (
        ('Основное', {
            'fields': ['domain', 'name', 'name_loct', 'name_dat', 'id_price'],
        }),
        ('Контакты', {
            'fields': ['address', 'email', 'phone', 'extra_phones', ('lat', 'lon')]
        }),
        ('SEO', {
            'fields': SeoAdminMixin.seo_fields + ['robots_txt', 'header_extra', 'footer_extra',
                                                  'seo_description_category', 'seo_description_product'],
        }),
    )
