from django.core.cache import cache


class CategoryCacheMixin:
    """
    Класс для кеширования категорий и связанных сущностей


    Позволяет кешировать товары для первой страницы категории.
    Нужно для вывода их по умолчанию до срабатывания аякса.

    FPP - сокращение от FIRST PAGE PRODUCTS

    FPP_KEY: str  ключ кеша
    FPP_QUANTITY: int количество товаров на первой странице
    FPP_TIMEOUT: int время жизни кеша 
        None - перманентно
        0 - не кешируется 
    """
    FPP_KEY = 'category-{}-products'
    FPP_QUANTITY = 30
    FPP_TIMEOUT = None

    def _get_fpp_from_db(self):
        return self.get_products()[:self.FPP_QUANTITY]

    def _get_or_set_cache_fpp(self):
        """ Метод для получения или сохрания товаров первой страницы

        Если товаров в кеше нет, то берем из бд и кешируем
        """
        key = self.FPP_KEY.format(self.pk)
        result = cache.get_or_set(key, self._get_fpp_from_db(), self.FPP_TIMEOUT)
        return result

    def clear_fpp_cache(self):
        cache.delete(self.FPP_KEY.format(self.pk))

    def get_fpp(self):
        """Метод получения товаров для первой страницы категории по умолчанию
        """
        return self._get_or_set_cache_fpp()

    def refresh_fpp_cache(self):
        """Метод обновления кеша страницы первых товаров
        """
        self.clear_fpp_cache()
        self.get_fpp()
        print(self, 'cache refreshing success')

    def refresh_fpp_cache_with_parents(self):
        """
        Метод обновления кеша страницы первых товаров и родителей категории
        """
        for item in self.get_ancestors(include_self=True):
            item.refresh_fpp_cache()

    @classmethod
    def refresh_fpp_cache_all(cls, only_active=False, rebuild=False):
        """Метод обновлния кеша первой страницы всех категорий
        only_active: bool только активные категории
        rebuild: bool пересобрать дерево категорий
        """
        queryset = cls.objects.all()
        if rebuild:
            cls.objects.rebuild()
        if only_active:
            queryset = queryset.filter(is_active=True)
        for item in queryset:
            item.refresh_fpp_cache()
