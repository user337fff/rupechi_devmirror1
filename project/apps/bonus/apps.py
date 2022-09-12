from django.apps import AppConfig


class BonusConfig(AppConfig):
    name = 'apps.bonus'
    verbose_name = 'Бонусная система'

    def ready(self):
        import apps.bonus.receivers
