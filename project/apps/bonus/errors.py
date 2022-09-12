class Error(Exception):
    pass


class ExceedsLimit(Error):
    pass


class InvalidAmount(Error):
    def __init__(self, amount):
        self.amount = amount

    def __str__(str):
        return f'Некорректная сумма: {self.amount}'


class InsufficientFunds(Error):
    def __init__(self, balance, amount):
        self.balance = balance
        self.amount = amount

    def __str__(self):
        return f'Сумма списания: {self.amount}, текущий баланс: {self.amount}'
