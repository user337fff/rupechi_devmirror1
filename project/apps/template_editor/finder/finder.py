import re
from pathlib import Path

from django.apps import apps
from django.conf import settings


def get_app_template_dirs(dirname):
    """
    Поиск директорий с шаблонами в приложениях

    !!! Функция скопирована чуть больше чем полностью 
        c django.template.utils.get_app_template_dirs
    !!! Сделано это чтобы в будущем модифицировать на группировку по приложениям
    """
    template_dirs = [
        Path(app_config.path) / dirname
        for app_config in apps.get_app_configs()
        if app_config.path and (Path(app_config.path) / dirname).is_dir()
    ]
    return tuple(template_dirs)



class TemplateFinder:
    """
    Класс для нахождения всех шаблонов проекта

    TEMPLATE_DIR_NAME:
        название директорий с шаблонами
    pre_templates_pattern:
        паттерн для удаления начальной части пути шаблона
    template_list:
        список шаблонов приложений
    template_dirs:
        список директорий с шаблонами
    """

    TEMPLATE_DIR_NAME = 'templates'

    pre_templates_pattern = re.compile(r'.+{}/'.format(TEMPLATE_DIR_NAME))

    def __init__(self):
        self.template_list = []
        self.template_dirs = self.get_template_dirs()

    def get_all_template_dirs(self):
        return get_app_template_dirs(self.TEMPLATE_DIR_NAME)

    def get_app_template_dirs(self):
        """
        Метод для получения директорий шаблонов только нашего проекта
        (без директорий подключаемых библиотек)
        """
        app_dirs = [
            template_dir
            for template_dir in self.get_all_template_dirs()
            if settings.BASE_DIR in str(template_dir)
        ]
        return app_dirs

    def get_template_dirs(self):
        """
        Метод для получения директорий шаблонов нашего проекта
        """
        dirs = self.get_app_template_dirs()
        dirs.append(settings.TEMPLATE_DIR)
        return dirs
    
    def filter_templates(self):
        """
        Метод для отсеивания ненужных шаблонов
        """
    
    def filter_asserts(self, template_name):
        """
        Метод для отсеивания ненужных шаблонов
        ______________________________________
        Arguments
        template_name:
            имя шаблона
        ______________________________________
        Return bool
        """
        return (
            self.__not_admin_assert(template_name) and
            self.__not_pages_content_assert(template_name)
            )
    
    def __not_admin_assert(self, template_name):
        if 'admin' in template_name:
            return False
        return True
    
    def __not_pages_content_assert(self, template_name):
        if 'pages/content' in template_name:
            return False
        return True

    def find(self):
        """
        Поиск шаблонов в директориях
        """
        for template_dir in self.template_dirs:
            self.template_list += [str(path) for path in Path(template_dir).glob('**/*.html')]
        self.template_list = [temp for temp in self.template_list if self.filter_asserts(temp)]
        self.template_list.sort()
        return self.template_list
    
    @classmethod
    def get_template_content_by_name(cls, template_name, template_list):
        """Получение содержимого шаблона по его имени"""
        template_path = cls.search_by_name(template_name, template_list)
        if template_path is not None:
            return cls.get_template_content(template_path)

    @classmethod
    def get_template_content(cls, template_path):
        """Получение содержимого шаблона"""
        with open(template_path, 'r') as file:
            return file.read()
    
    @classmethod
    def set_template_content(cls, template_path, content):
        """Изменение содержимого шаблона"""
        with open(template_path, 'w') as file:
            file.write(content)
    
    @classmethod
    def search_by_name(cls, template_name, template_list):
        """Поиск шаблона по имения(неполному пути)"""
        for template in template_list:
            if template_name in template:
                return template
        return
    
    @classmethod
    def trim_pre_path(cls, path):
        """Удаление из пути первой части"""
        return cls.pre_templates_pattern.sub('', path)