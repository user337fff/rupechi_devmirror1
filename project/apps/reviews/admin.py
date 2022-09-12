from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin

from apps.reviews.models import Review


@admin.register(Review)
class ReviewsAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['__str__', 'is_active']

    def get_queryset(self, request):
        return super(ReviewsAdmin, self).get_queryset(request).filter(product=None)
