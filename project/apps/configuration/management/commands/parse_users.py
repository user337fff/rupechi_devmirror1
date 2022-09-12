from apps.users.models import Account
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        data = []
        for item in data:
            item['phone'] = item['phone'] or ''
            user = Account.objects.filter(email=item.get('email')).first()
            if user:
                user.contractor = item.get('contractor')
                user.save(update_fields=['contractor'])
                print('Обновлен', user)
            else:
                user = Account.objects.create(**item)
                print('Создан', user)
