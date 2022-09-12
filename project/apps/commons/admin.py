from django.contrib import admin, messages
from django.core.cache import cache
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html

from apps.domains.models import Domain


class ClearCacheSlugMixin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        response = super().save_model(request, obj, form, change)
        if hasattr(obj, 'tree_id'):
            print(f'=====OBJ TREE ID {obj.tree_id}')
            items = obj.__class__.objects.filter(tree_id=obj.tree_id)
            print(f'======OBJ TREE ITEMS {items}')
        else:
            items = [obj]
        keys = []
        for domain in Domain.objects.iterator():
            for item in items:
                key_slug = item.get_key_slug(domain=domain)
                keys += [key_slug]
        cache.delete_many(keys)
        return response


class ImageFilter(admin.SimpleListFilter):
    """ Фильтр для картинки  """
    title = 'Картинка'
    parameter_name = 'with_image'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С картинкой'),
            ('no', 'Без картинки'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'yes':
            return queryset.filter(image__gt=0)
        elif value == 'no':
            return queryset.exclude(image__gt=0)
        return queryset


class ImageModelAdmin(admin.ModelAdmin):
    list_filter = [ImageFilter]

    def save_model(self, request, obj, form, change, gallery_data=None):
        super(ImageModelAdmin, self).save_model(request, obj, form, change)
        if 'image' in form.changed_data:
            # вычисляем и записываем хэш новой картинки
            obj.calc_image_hash()

        if gallery_data is not None:
            # Мультизагрузка картинок в связанную модель
            InlineModel = gallery_data['inline_model']
            if gallery_data['gallery_field'] in form.changed_data:
                for image_file in request.FILES.getlist(gallery_data['gallery_field']):
                    image = InlineModel(image=File(image_file))
                    setattr(image, gallery_data['foreign_key'], obj)
                    image.calc_image_hash(save=False)
                    image.save()

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(
            super(ImageModelAdmin, self).get_readonly_fields(request, obj))
        # добавляем в поля только для чтения хэш картинки
        readonly_fields.append('image_md5')
        return readonly_fields

    def get_image(self, obj):
        if obj.image:
            return format_html('<img style="height: 70px;" src="{}">',
                               obj.image_m.url)
        return ''

    get_image.short_description = 'Картинка'
    get_image.admin_order_field = 'image'


class ExportExcelAdmin(admin.ModelAdmin):
    """
    Модель панели администратора с кнопкой экспорта

    При наследовании требуется переопределить параметры change_list_template
    и export_model

    change_list_template - путь до шаблона с кнопкой экспорта
    export_model - модель, наследник класса ExportLimiter

    """
    change_list_template = None
    export_model = None

    def export_url(self):
        return f"export-{self.model._meta.model_name}/"

    def get_urls(self):
        urls = super().get_urls()
        my_urls: list = [
            path(self.export_url(), self.export_xlsx),
        ]
        return my_urls + urls

    def export_xlsx(self, request):
        unlock_after, export_file = self.export_model.export(request.user)
        if unlock_after > 0:
            message = f"Экспорт будет доступен через {unlock_after} сек."
            self.message_user(request, message, messages.ERROR)
            return HttpResponseRedirect('../')
        now = timezone.now()
        response = HttpResponse(export_file.getvalue())
        response[
            "mimetype"
        ] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        content_dis = f"attachment;filename={self.model._meta.model_name}{now:%H-%m_%d-%M-%Y}.xlsx"
        response["Content-Disposition"] = content_dis
        return response


class SingletonAdmin(admin.ModelAdmin):
    # def __init__(self, model, admin_site):
    #     super().__init__(model, admin_site)
    #     # try для корректного создания миграция в бд
    #     try:
    #         model.load().save()
    #     except ProgrammingError:
    #         pass

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
