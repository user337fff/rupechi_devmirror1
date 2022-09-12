class Error(Exception):
    pass


class FileUndefined(Error):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return f'Файл не найден: {self.filename}'


class GroupUndefined(Error):
    def __init__(self, id_1c=None):
        self.id_1c = id_1c

    def __str__(self):
        return f'Товар не имеет категории: {self.id_1c}'
