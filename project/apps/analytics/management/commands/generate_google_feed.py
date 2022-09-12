from apps.analytics.google import GoogleFeedGenerator
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(*args, **options):
        GoogleFeedGenerator().generate()
