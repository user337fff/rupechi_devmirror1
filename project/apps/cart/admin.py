from django.contrib import admin

from jet.admin import CompactInline
from .models import Cart, CartItem


class CartItemAdmin(CompactInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ('product',)


class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemAdmin, ]
    readonly_fields = ('user', )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(CartAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


admin.site.register(Cart, CartAdmin)
