from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django.contrib import admin

from .models import (HeaderMenuItem, FooterMenuItem, SidebarMenuItem, MenuSubItem, CatalogMenuItem)


class MenuSubItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = MenuSubItem


@admin.register(CatalogMenuItem)
@admin.register(SidebarMenuItem)
@admin.register(FooterMenuItem)
@admin.register(HeaderMenuItem)
class BaseMenuAdmin(SortableAdminMixin, admin.ModelAdmin):
    exclude = ('location',)
    inlines = [MenuSubItemInline]
