from django.core.management import BaseCommand
from django.db import transaction

from apps.shop.models import Order
from apps.feedback.models import Emails
from apps.feedback.mailer import Mailer


class Command(BaseCommand):

    def get_receivers(self, order):
        receivers = []
        for item in order.items.all():
            receivers.extend(list(set(item.product.category.get_ancestors(include_self=True)
                                      .values_list('receivers', flat=True))))
        return receivers

    @transaction.atomic
    def send_all_notifications(self):
        emails = Emails.objects.all()
        for email in emails:
            Mailer.send(email.subject, email.text, email.message, email.from_mail, list(email.recipients))
            email.delete()

    def handle(self, *args, **options):
        self.send_all_notifications()
