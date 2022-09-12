
ТРЕБУЕМЫЕ ПРИЛОЖЕНИЯ:
1. catalog


ПОДКЛЮЧЕНИЕ:
1. В settings добавляем context_processor:
    "apps.compare.context_processors.compare",
2. В urls добавляем:
    path("compare/", include("apps.compare.urls", namespace='compare')),

