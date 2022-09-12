from apps.domains.models import Domain
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Переименовать домен'

    def add_arguments(self, parser):
        parser.add_argument('old', type=str)
        parser.add_argument('new', type=str)

    def handle(self, *args, **options):
        old_domain_name = options.get('old')
        new_domain_name = options.get('new')
        # Копирование домена
        domain = Domain.objects.filter(domain=new_domain_name).first()
        old_domain = Domain.objects.filter(domain=old_domain_name).first()
        if old_domain is None:
            raise CommandError('Домен "%s" не найден' % old_domain_name)
        if not domain:
            domain = Domain(domain=new_domain_name)
            for key, value in Domain.objects.filter(domain=old_domain_name).values()[0].items():
                if key in ['domain']:
                    continue
                setattr(domain, key, value)
            domain.save()

        data = {
            'domains': set(),
            'domain': set(),
        }
        for name in {item.get_accessor_name() for item in old_domain._meta.related_objects}:
            for obj in getattr(old_domain, name).iterator():
                for k in ['domain', 'domains']:
                    v = getattr(obj, k, None)
                    if v:
                        if hasattr(v, 'all'):
                            v.add(domain)
                            v.remove(old_domain)
                            print(obj, 'Обновлено')
                        else:
                            data[k].add(name)
                        break

        for k, related in data.items():
            for relate in related:
                getattr(old_domain, relate).update(domain=domain)
                print(relate, 'Обновлено')
        old_domain.delete()