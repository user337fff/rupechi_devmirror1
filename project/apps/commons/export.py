import io
import os
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils import timezone

import xlsxwriter


class ExportLimiter(models.Model):
    """ 
    Время последнего экспорта в Excel 

    Для экспорта требуется передать в метод export коллбэк,
    который возвращает файл, либо байтовый массив.
    Так же можно перегрузить метод следющим образом:
    def export(params):
        return super().export(user, self.export2bytes)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="Пользователь", on_delete=models.CASCADE)
    date_last_export = models.DateTimeField(
        verbose_name="Дата последнего экспорта", default=timezone.now)

    PERIOD_REPEAT = 60 * 2

    def __str__(self) -> str:
        return f"{self.user} {self.date_last_export}"

    def unlock_after(self) -> int:
        """ Экспорт станет доступным через """
        period_repeat = timedelta(seconds=self.PERIOD_REPEAT)
        delta = self.date_last_export + period_repeat - timezone.now()
        return int(delta.total_seconds())

    @classmethod
    def export(cls, user: settings.AUTH_USER_MODEL, callback):
        """
        returned params:
         - unlock after * seconds
         - file xlsx
        """
        last_export, _created = cls.objects.get_or_create(user=user)
        unlock_after = last_export.unlock_after()
        if _created or unlock_after < 0:
            last_export.date_last_export = timezone.now()
            last_export.save(update_fields=['date_last_export'])
            return 0, callback()
        return unlock_after, None

    class Meta:
        abstract = True


class ExportXlsx:
    """
    Экспорт в файл Excel

    folder - каталог для файлов экспорта
    file_prefix - префикс файла экспорта

    При наследовании можно переопределить только метод _export,
    основные методы export2file, export2bytes будут работать

    """

    # folder = "users/xlsx/"
    # file_prefix = "users"
    folder = None
    file_prefix = None
    extension = "xlsx"

    def _set_filename(self):
        now = timezone.now().strftime("%H-%M_%d-%m-%Y")
        self.filename = f"{self.file_prefix}_{now}.{self.extension}"

    def _set_filepath(self):
        folder_path = os.path.join(settings.MEDIA_ROOT, self.folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        self._set_filename()
        self.filepath = os.path.join(folder_path, self.filename)
        return self.filepath

    def _export(self):
        worksheet = self.workbook.add_worksheet()
        worksheet.set_column(0, 0, 40)
        worksheet.set_column(1, 1, 35)
        worksheet.set_column(2, 2, 20)
        # Заголовок таблицы
        headline = self._get_headline()
        for col, item in enumerate(headline):
            worksheet.write(0, col, item)
        users = self.get_users()
        print(users)
        for row, user in enumerate(users, 1):
            print(user.name, user.email)
            worksheet.write(row, 0, user.name)
            worksheet.write(row, 1, user.email)
            worksheet.write(row, 2, user.phone)
            if self.shop_exist:
                worksheet.write(row, 3, user.get_orders())
                worksheet.write(row, 4, user.get_total_orders())
                worksheet.write(row, 5, user.get_cart())

        self.workbook.close()
        return self.result

    def export2file(self) -> str:
        """
        returned media url
        """
        filepath = self._set_filepath()
        self.workbook = xlsxwriter.Workbook(filepath)
        self.result = f"{settings.MEDIA_URL}{self.folder}{self.filename}"
        return self._export()

    def export2bytes(self) -> io.BytesIO:
        """
        returned bytesarray
        """
        self.xlsx_file = io.BytesIO()
        self.workbook = xlsxwriter.Workbook(
            self.xlsx_file, {"in_memory": True})
        self.result = self.xlsx_file
        return self._export()
