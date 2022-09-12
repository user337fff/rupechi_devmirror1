from django.apps import AppConfig


class CommonsConfig(AppConfig):
    name = 'apps.commons'

    def ready(self):
        import apps.commons.signals
