
ТРЕБУЕМЫЕ ПРИЛОЖЕНИЯ:
1. catalog


ПОДКЛЮЧЕНИЕ:
1. В settings добавляем context_processor:
    "apps.wishlist.context_processors.wishlist",
2. В urls добавляем:
    path("wishlist/", include("apps.wishlist.urls", namespace='wishlist'))


ПРИМЕЧАНИЕ:
Страница избранных товаров использует шаблон карточки товара:
'catalog/product_card.html'



path("compare/", include("apps.compare.urls", namespace='compare')),