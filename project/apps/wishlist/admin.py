from django.contrib import admin

from apps.wishlist.models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    pass
