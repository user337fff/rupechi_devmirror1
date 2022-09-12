from django.core.management.base import BaseCommand
from apps.analytics.yandex import YandexFeedGenerator

class Command(BaseCommand):

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--domain',
            default=""
        )

    def handle(*args, **options):

        if(options["domain"]):
            YandexFeedGenerator().generate(options["domain"])
        else:
            YandexFeedGenerator().generate()