"""
Команда импорта прав на доступ к моделям из приложений для разных типов групп.
Для импорта прав приложение должно содержать файл permissions.py.
Файл содержит словарь PERMISSIONS.
Ключи словаря - название групп.
Значения - список прав на модели в формате: ["action_model",]

Пример:

PERMISSIONS = {
                "admin": ["add_user", "change_user",
                          "delete_user", "view_user"]
                "content-admin": [...],
                 ...
              }

"""
import importlib

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps as django_apps
from django.conf import settings


def dynamic_import(module):
    """ Импорт модуля """
    try:
        m = importlib.import_module(module)
    except ImportError as e:
        m = None
        print("Module:", module, e)
    return m


class Command(BaseCommand):
    help = 'Set permissions for user-groups'

    APP_LABELS = [app_name.split(".")[-1] for app_name in settings.CUSTOM_APPS]
    groups_names = ["admin", "content-admin", "editor", "manager"]
    groups = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_groups()

    def init_groups(self):
        """ Получаем объекты групп  """
        print("GROUPS INIT")
        for group_name in self.groups_names:
            group, _ = Group.objects.get_or_create(name=group_name)
            self.groups.append(group)
            print(f"- '{group_name}' inited")

    def add_arguments(self, parser):
        parser.add_argument(
            '-a',
            '--apps',
            nargs='+',
            help='List of apps labels for importing permissions. '
                 'Example: "catalog"', required=False)

    def handle(self, *args, **options):

        if options['apps']:
            self.APP_LABELS = options['apps']

        for app_label in self.APP_LABELS:
            self.import_app_perms(app_label)

    def import_app_perms(self, app_label: str):
        app_name = django_apps.get_app_config(app_label).name
        # Импортируем права на модели приложения
        perm_module = dynamic_import(f"{app_name}.permissions")
        if perm_module is not None:
            permissions = perm_module.PERMISSIONS
            print("App:", app_label)
            # Объекты моделей приложения в контент фреймворке
            content_models = ContentType.objects.filter(app_label=app_label)
            print("- Сontent models: ", content_models)
            for group in self.groups:
                group_perms = permissions.get(group.name)
                print("-- ", group, "Perms:", group_perms)
                if group_perms:
                    # Полуаем права для моделей приложения, для всех групп
                    perms = Permission.objects.filter(
                        content_type__in=content_models,
                        codename__in=group_perms
                    )
                    group.permissions.add(*perms)
