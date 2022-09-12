from adminsortable2.admin import SortableInlineAdminMixin, CustomInlineFormSet, SortableAdminMixin
from apps.commons.admin import ImageModelAdmin, ImageFilter, ClearCacheSlugMixin
from apps.commons.widgets import MultiImageField
from apps.domains.models import Domain
from apps.bonus.models import BonusCategory
from apps.seo.admin import SeoAdminMixin
from django import forms
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.widgets import AutocompleteSelect
from django.db.models import Count
from django.db.models import Q, F
from django.utils import timezone
from mptt.admin import DraggableMPTTAdmin
from copy import deepcopy

from . import models as catalog
from .models.category import SLUG_PRICE, Category, Alias, Catalog, CategoryAttribute, \
    SeoCategory, SlugCategory, AlterSeoCategory

from ..reviews.models import Review
from ..stores.models import StoreProductQuantity


class CategoryAttrAdmin(SortableInlineAdminMixin, admin.TabularInline):
    model = catalog.CategoryAttribute


class AliasAttrInline(SortableInlineAdminMixin, admin.TabularInline):
    model = catalog.AliasAttribute


class SlugCategoryInline(admin.TabularInline):
    model = catalog.SlugCategory


class RatingInline(admin.TabularInline):
    model = catalog.Rating


class MessageCategoryInline(admin.TabularInline):
    model = catalog.MessageCategory


class PricesInline(admin.TabularInline):
    model = catalog.Prices


class ProductVideoInline(admin.TabularInline):
    model = catalog.ProductVideo


class ProductDocumentInline(admin.TabularInline):
    model = catalog.ProductDocument


class SeoInline(admin.StackedInline):
    model = catalog.SeoCategory
    extra = 0


class ReplaceFormAttr(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReplaceFormAttr, self).__init__(*args, **kwargs)
        self.fields['attribute'].queryset = self.fields['attribute'].queryset.exclude(id_1c=None)

    class Meta:
        model = catalog.ReplaceAttr
        exclude = []


@admin.register(catalog.ReplaceAttr)
class ReplaceAttrAdmin(admin.ModelAdmin):
    form = ReplaceFormAttr


@admin.register(CategoryAttribute)
class CategoryAttributeAdmin(SortableAdminMixin, admin.ModelAdmin):
    exclude = ['category']

    def get_queryset(self, request):
        return self.model.objects.filter(category__isnull=True)


@admin.register(Catalog)
class BaseCatalogAdmin(DraggableMPTTAdmin, ClearCacheSlugMixin, ImageModelAdmin):
    list_display = ('tree_actions', 'indented_title', 'get_image', 'get_domains')
    list_display_links = ('indented_title',)
    list_filter = ('is_active', ImageFilter, 'updated_at', 'domain')
    search_fields = ('title',)
    readonly_fields = ('image_md5', 'id_1c', 'updated_at', 'created_at',)
    # list_per_page = 50
    save_on_top = True
    alias_block = ('Алиас', {
        'fields': ('brands', 'search'),
    })

    fieldsets = (
        ('Информация', {
            'classes': ('wide', 'extrapretty'),
            'fields': ('domain', 'parent', 'is_active', 'show_on_menu', 'show_on_categories', 'is_index', 'is_hide', 'unlink_brand', 'visible_mounting',
                       'title', 'short_title', 'description', 'product_description', 'type', 'image',
                       'image_md5', 'updated_at', 'created_at', 'webp_image')
        }),
        ('Импорт/экспорт', {
            'classes': ('collapse',),
            'fields': ('id_1c',),
        }),
        ('Настройки', {
            'fields': (('saved_attrs_children', 'saved_attrs_parent', 'dont_save_attrs_parent'), 'discount_brands',
                       'discount_brands_save_child')
        }),
        alias_block,
        ('Общее SEO', {
            'fields': SeoAdminMixin.seo_fields
        }),
    )
    inlines = [SeoInline, CategoryAttrAdmin, AliasAttrInline, SlugCategoryInline]

    def get_domains(self, obj):
        return ', '.join(obj.domain.values_list('name', flat=True))

    get_domains.short_description = 'Домены'
    get_domains.admin_order_field = 'domain'





@admin.register(Category)
class CategoryAdmin(BaseCatalogAdmin):
    fieldsets = (
        ('Информация', {
            'classes': ('wide', 'extrapretty'),
            'fields': ('domain', 'receivers', 'parent', 'is_active', 'is_index', 'is_hide', 'discount_category', 'unlink_brand', 'visible_mounting',
                       'title', 'description', 'product_description', 'type', 'image',
                       'image_md5', 'updated_at', 'created_at', 'hit_check_products')
        }),
        ('Импорт/экспорт', {
            'classes': ('collapse',),
            'fields': ('id_1c',),
        }),
        ('Настройки', {
            'fields': (('saved_attrs_children', 'saved_attrs_parent', 'dont_save_attrs_parent'), 'discount_brands',
                       'discount_brands_save_child')
        }),
        ('Общее SEO', {
            'fields': SeoAdminMixin.seo_fields
        }),
    )
    inlines = [CategoryAttrAdmin, MessageCategoryInline, SeoInline, SlugCategoryInline]


def copy_alias(modeladmin, request, queryset):
    for obj in queryset:
        new_obj = deepcopy(obj)
        new_obj.domain.set(obj.domain.all())
        new_obj.discount_category.set(obj.discount_category.all())
        new_obj.show_on_categories.set(obj.show_on_categories.all())
        new_obj.brands.set(obj.brands.all())
        new_obj.discount_brands.set(obj.discount_brands.all())
        new_obj.alias_products.set(obj.alias_products.all())
        new_obj.pk = None
        new_obj.save()
        foreign_models = [CategoryAttribute, SeoCategory, SlugCategory, BonusCategory]
        for model in foreign_models:
            new_models = model.objects.filter(category=obj)
            for new_model in new_models:
                new_model.pk = None
                new_model.category = new_obj
                new_model.save()

copy_alias.short_description = "Копировать выбранные алиасы"


@admin.register(Alias)
class AliasAdmin(BaseCatalogAdmin):
    actions = [copy_alias]


@admin.register(AlterSeoCategory)
class AlterSeoCategoryAdmin(admin.ModelAdmin):

    class Meta:
        model = AlterSeoCategory


class CollectionAdmin(ImageModelAdmin):
    list_display = ('title', 'get_image', 'is_active')
    list_filter = ('is_active', ImageFilter)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('updated_at', 'created_at')
    autocomplete_fields = ("products",)

    fieldsets = (
        ('Информация', {
            'classes': ('wide', 'extrapretty'),
            'fields': ('is_active', 'title',
                       'slug', 'description', 'image',
                       'image_md5', 'products', 'updated_at', 'created_at')
        }),
        ('SEO', {
            'fields': SeoAdminMixin.seo_fields
        })
    )


class CollectionInline(admin.TabularInline):
    model = catalog.Collection.products.through
    verbose_name = "Коллекция"
    verbose_name_plural = "Коллекции"


class ProductInlineFormset(CustomInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super(ProductInlineFormset, self).save_new(form, commit=False)
        if commit:
            obj.save()
        obj.calc_image_hash(save=True)
        return obj

    def save(self, commit=True):
        instances = super(ProductInlineFormset, self).save(commit)
        if commit:
            for instance in instances:
                instance.calc_image_hash(save=False)
                instance.save()
        return instances


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = catalog.ProductImage
    formset = ProductInlineFormset
    readonly_fields = ('image_md5',)
    fields = ['image']
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(
            request, obj, **kwargs)
        formset.request = request
        return formset


class AttributeValueAdmin(admin.ModelAdmin):
    search_fields = ('value',)


class CustomModelChoiceField(forms.ModelChoiceField):
    def validate(self, value):
        pass

    def to_python(self, value):
        if value in self.empty_values:
            return None
        return value


class CustomAutocomplete(AutocompleteSelect):
    def optgroups(self, name, value, attrs=None):
        return []


class AttributeProductForm(forms.ModelForm):
    """
    Форма для заполнения значения атрибута
    Модель значения  имеет два поля value_dict и value_number
    value - поле, значение которого попадает в то или иное поле модели
            в зависимости от типа выбранного атрибута
    """

    value = CustomModelChoiceField(
        queryset=catalog.AttributeValue.objects.all(),
        widget=CustomAutocomplete(catalog.AttributeProducValue._meta.get_field(
            'value_dict').remote_field, admin.site, attrs={'data-tags': 'true'}),
        to_field_name='value'
    )

    class Meta:
        model = catalog.AttributeProducValue
        fields = ('attribute', 'value')


class AttributeProductValueInline(SortableInlineAdminMixin, admin.TabularInline):
    model = catalog.AttributeProducValue
    extra = 0


class ProductForm(forms.ModelForm):
    gallery = forms.FileField(widget=MultiImageField, required=False)

    class Meta:
        model = catalog.Product
        fields = '__all__'


class StoresInline(admin.TabularInline):
    model = StoreProductQuantity
    extra = 0


class ReviewsInline(admin.StackedInline):
    model = Review
    extra = 3

class InStockNotificationInline(admin.TabularInline):
    model = catalog.InStockNotification

class ProductAdmin(DraggableMPTTAdmin, ImageModelAdmin):
    list_display = ('tree_actions', 'indented_title', 'get_image', 'category', 'is_active')
    list_filter = ('category', 'domain', 'is_active', ImageFilter)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('id_1c', 'discount_price', 'updated_at', 'created_at', 'views')
    search_fields = ('title', 'slug', 'id_1c')
    autocomplete_fields = ('related_products',)
    form = ProductForm
    list_select_related = ['category']
    list_per_page = 50

    fieldsets = (
        ('Информация', {
            'classes': ('wide', 'extrapretty'),
            'fields': ('domain', 'category', 'is_active', 'is_discount', 'title',
                       ('hit', 'new', 'offer', 'top_hit'),
                       'slug', 'brand', 'description', 'image',
                       'image_md5', 'related_products', 'keywords',
                       'updated_at', 'created_at', 'views')
        }),
        ('Импорт/экспорт', {
            'classes': ('collapse',),
            'fields': ('id_1c',),
        }),
        ('Загрузка картинок', {
            'fields': ('gallery',),
        }),
        ('Габариты', {
            'fields': ('weight', 'width', 'height', 'length'),
        }),
        ('SEO', {
            'fields': SeoAdminMixin.seo_fields
        })
    )

    inlines = (
        ProductImageInline, AttributeProductValueInline, StoresInline,
        PricesInline, RatingInline, ReviewsInline,
        ProductVideoInline, ProductDocumentInline, InStockNotificationInline)
    actions = ['copy_product']
    save_on_top = True

    class Media:
        js = ("catalog/js/admin_product.js",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category') \
            .filter(
            Q(variations__domain__exact=request.domain)
            | Q(domain__exact=request.domain)
            | Q(domain__isnull=True)
        ) \
            .distinct()

    def save_model(self, request, obj, form, change, **kwargs):
        gallery = {
            'inline_model': catalog.ProductImage,
            'gallery_field': 'gallery',
            'foreign_key': 'product'
        }
        super().save_model(request, obj, form, change, gallery)
        # обновляем кеш первой страницы категории
        if 'category' in form.changed_data and obj.category:
            obj.category.refresh_fpp_cache_with_parents()

    def copy_product(self, request, queryset):
        for product in queryset:
            attributes = product.product_attributes.all()
            images = product.gallery.all()
            product.pk = None  # копируем товар и к слагу прибавляем id, сохраняем
            product.slug += str(timezone.now().timestamp())
            try:
                product.save()
            except:
                self.message_user(
                    request, "Товар с таким слагом уже существует", level=messages.ERROR)
                return

            for attr in attributes:
                attr.pk = None
                attr.product = product
                attr.save()

            for image in images:
                image.pk = None
                image.product = product
                image.save()
        self.message_user(
            request, "Товары успешно скопированы", level=messages.SUCCESS)

    copy_product.short_description = 'Копировать выбранные товары'

    def discount_price(self, obj):
        if obj is not None and obj.old_price > 0:
            return str(round((1 - obj.price / obj.old_price) * 100)) + ' %'
        return '-'

    discount_price.short_description = 'Размер скидки'


class BrandAdmin(ImageModelAdmin):
    save_on_top = True
    list_display = ('title', 'get_image', 'is_active')
    list_filter = ('is_active', ImageFilter)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('updated_at', 'created_at')

    fieldsets = (
        ('Информация', {
            'classes': ('wide', 'extrapretty'),
            'fields': ('id_1c', 'is_active', 'is_index', 'domain', 'title',
                       'slug', 'not_discount', 'description', 'image',
                       'image_md5', 'updated_at', 'created_at')
        }),
        ('SEO', {
            'fields': SeoAdminMixin.seo_fields + ['meta_message']
        })
    )


@admin.register(catalog.ProductAttribute)
class ProductAttributeAdmin(SortableAdminMixin, admin.ModelAdmin):
    stock_fields = [SLUG_PRICE, 'brand', 'stock']

    prepopulated_fields = {"slug": ("title",)}

    def get_readonly_fields(self, request, obj=None):
        fields = []
        if obj and obj.slug in self.stock_fields:
            fields = ['slug', 'type', 'id_1c']
        return fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.slug in self.stock_fields:
            return False
        return super(ProductAttributeAdmin, self).has_delete_permission(request, obj)


class CalcItemInline(SortableInlineAdminMixin, admin.TabularInline):
    model = catalog.CalcItem


@admin.register(catalog.Calc)
class CalcAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'diameter', 'pipe', 'brand']
    inlines = [CalcItemInline]


admin.site.register(catalog.Product, ProductAdmin)
admin.site.register(catalog.Collection, CollectionAdmin)
admin.site.register(catalog.Brand, BrandAdmin)
admin.site.register(catalog.AttributeValue, AttributeValueAdmin)
admin.site.register(catalog.AttributeProducValue)