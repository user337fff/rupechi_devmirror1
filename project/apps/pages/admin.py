from adminsortable2.admin import SortableInlineAdminMixin
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from jet.admin import CompactInline
from mptt.admin import DraggableMPTTAdmin

from apps.seo.admin import SeoAdminMixin
from . import models as pages_models
from ..commons.admin import ClearCacheSlugMixin


class TextBlockInline(CompactInline):
    model = pages_models.TextBlock
    extra = 0


class SpoilerInline(CompactInline):
    model = pages_models.SpoilerBlock
    extra = 0


class TitleLinkInline(CompactInline):
    model = pages_models.TitleLinkBlock
    extra = 0
    fk_name = "page"


class FormInline(CompactInline):
    model = pages_models.FormBlock
    extra = 0


class PagesInline(CompactInline):
    model = pages_models.Pages
    extra = 0


class PagesBlockItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = pages_models.PagesBlockItem


@admin.register(pages_models.PagesBlock)
class PagesBlockAdmin(admin.ModelAdmin):
    inlines = [PagesBlockItemInline]


@admin.register(pages_models.PagesBlockItem)
@admin.register(pages_models.FormBlock)
@admin.register(pages_models.TitleLinkBlock)
@admin.register(pages_models.SpoilerBlock)
class ComponentAdmin(admin.ModelAdmin):
    pass


# class ShortTextForm(forms.ModelForm):
#     type = forms.ChoiceField(
#         choices=pages_models.ShortTextBlock.TYPES, label='type', widget=forms.Select)

#     class Meta:
#         model = pages_models.ShortTextBlock
#         fields = '__all__'


class ShortTextBlockInline(CompactInline):
    model = pages_models.ShortTextBlock
    extra = 0
    # form = ShortTextForm


class FilesInline(CompactInline):
    model = pages_models.Files
    extra = 0


class ProductsInline(CompactInline):
    model = pages_models.Products
    extra = 0


class SliderInline(CompactInline):
    model = pages_models.Slider
    extra = 0


class GalleryInline(CompactInline):
    model = pages_models.Gallery
    extra = 0


class ReviewsInline(CompactInline):
    model = pages_models.Reviews
    extra = 0


class BasePageAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    change_form_template = 'admin/pages/page/change_form.html'

    inlines = [
        TextBlockInline,
        ShortTextBlockInline,
        FilesInline,
        ProductsInline,
        SliderInline,
        GalleryInline,
        ReviewsInline,
        SpoilerInline,
        TitleLinkInline,
        FormInline,
        PagesInline,
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = super(BasePageAdmin, self).get_readonly_fields(obj)
        if obj and obj.template:
            fields = list(set(list(fields) + ['template']))
        return fields


class PageAdmin(DraggableMPTTAdmin, ClearCacheSlugMixin, BasePageAdmin):
    list_display = ['tree_actions', 'indented_title', 'is_active', 'template', 'get_domains']
    readonly_fields = ['get_domains', 'created_at', 'updated_at']
    exclude = ('type', 'heading')
    list_filter = ['domain']
    sortable = 'sort'
    fieldsets = (
        (None, {
            'fields': ('domain', 'parent', 'is_active', 'title', 'full_title', 'description', 'slug', 'template',
                       'image', 'has_sidebar', 'pub_date', 'created_at', 'updated_at')
        }),
        ('SEO', {
            'fields': SeoAdminMixin.seo_fields
        })
    )

    def get_queryset(self, request):
        return super(PageAdmin, self).get_queryset(request).prefetch_related('domain')

    def get_domains(self, obj):
        return ', '.join([domain for domain in obj.domain.values_list('name', flat=True)])

    get_domains.short_description = 'Домены'
    get_domains.admin_order_fields = 'domain'


class PostForm(forms.ModelForm):
    class Meta:
        model = pages_models.Post
        exclude = ('type',)

    def clean_heading(self):
        data = self.cleaned_data['heading']
        if not data:
            raise forms.ValidationError(_("Обязательное поле."))
        return data


class PostAdmin(BasePageAdmin):
    form = PostForm
    list_filter = ('heading', 'is_active')

    fieldsets = (
        (None, {
            'fields': ('is_active', 'heading',
                       'title', 'full_title', 'slug', 'pub_date',
                       'created_at', 'updated_at')
        }),
        ('SEO', {
            'fields': SeoAdminMixin.seo_fields
        })
    )


class FilesBlockItemInline(admin.TabularInline):
    model = pages_models.FilesBlockItem


class FilesBlockAdmin(admin.ModelAdmin):
    inlines = [FilesBlockItemInline, ]


class GalleryBlockItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = pages_models.GalleryBlockItem


class GalleryBlockAdmin(admin.ModelAdmin):
    inlines = [GalleryBlockItemInline, ]


class SliderBlockItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = pages_models.SliderBlockItem


class SliderBlockAdmin(admin.ModelAdmin):
    inlines = [SliderBlockItemInline, ]


class ProductsBlockForm(forms.ModelForm):
    """
    См. README
    """

    class Meta:
        model = pages_models.ProductsBlock
        fields = '__all__'

    def clean(self):
        """
        Проверка поля с товаром на существование
        """
        product = pages_models.ProductsBlockItem.product
        if product is None:
            raise forms.ValidationError(
                "Для использования установите модуль каталога")
        return self.cleaned_data


class ProductsBlockItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = pages_models.ProductsBlockItem


class ProductsBlockAdmin(admin.ModelAdmin):
    inlines = [ProductsBlockItemInline, ]
    form = ProductsBlockForm


class ReviewsBlockItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = pages_models.ReviewsBlockItem


class ReviewsBlockAdmin(admin.ModelAdmin):
    inlines = [ReviewsBlockItemInline, ]


admin.site.register(pages_models.Heading)
admin.site.register(pages_models.Page, PageAdmin)
admin.site.register(pages_models.Post, PostAdmin)
admin.site.register(pages_models.TextBlock)
admin.site.register(pages_models.ShortTextBlock)
admin.site.register(pages_models.FilesBlock, FilesBlockAdmin)
admin.site.register(pages_models.ProductsBlock, ProductsBlockAdmin)
admin.site.register(pages_models.SliderBlock, SliderBlockAdmin)
admin.site.register(pages_models.GalleryBlock, GalleryBlockAdmin)
admin.site.register(pages_models.ReviewsBlock, ReviewsBlockAdmin)
