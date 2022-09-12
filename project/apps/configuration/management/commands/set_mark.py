import random

from apps.catalog.models import *
from apps.users.models import Account
from django.core.management.base import BaseCommand
from django.db.models import Max


class Command(BaseCommand):
    """
    1. Оценка есть у половины товаров на листинге.
    2. Из них - половина это 5 звёзд, вторая половина - 4 звезды. Оценка 3 звезды попадается 1 раз на 2-3 листинга.
    3. Оценок на каждом товаре - от 1 до 10.
    4. Чем дороже товар, тем меньше у него оценок и выше рейтинг.
    5. У товаров дороже 50 тыс. - оценки только 5, количество оценок от 1 до 4, не больше.
    Ps: Как вообще 4 и 5 пункт могут не противоречить 1 2 3
    """
    help = 'Установка рейтинга'
    min_count = 1
    max_count = 10
    max_rate = 5

    def handle(self, *args, **options):
        Rating.objects.filter(user__email__startswith='user_').delete()
        qs = Product.objects.annotate(calc_price=Min('prices__price')).filter(calc_price__gt=0)[::2]
        # max_price = products.aggregate(max_price=Max('calc_price'))['max_price'] or 0
        max_product_price = decimal.Decimal(50000)
        kk = 0
        cc = 0
        for index, product in enumerate(qs):
            divider = 30
            price = product.calc_price or 0
            # if index % divider == 0 and price < max_product_price:
            #     # Оценка 3 звезды попадается 1 раз на 2-3 листинга.
            #     rate = 3
            #     count = random.randint(1, 2)
            #     self.set_rating(product, rate, count)
            #     kk += 1
            #     continue
            # У товаров дороже 50 тыс. - оценки только 5, количество оценок от 1 до 4, не больше.
            if price >= max_product_price:
                rate = random.randint(4, 5)
                if cc == 1:
                    rate = 5
                    cc = 0
                if rate == 4:
                    cc += 1
                count = random.randint(1, 4)
                self.set_rating(product, rate, count)
            else:
                rate = (self.max_rate / max_product_price * product.calc_price) + 2
                if rate > 5:
                    rate = 5
                count = random.randint(1, 10)
                self.set_rating(product, rate, count)
            kk += 1
        print(f'Всего товаров оценено {kk}')

    def set_rating(self, product, rate, count=1):
        rate = round(float(rate) + 0.1) # Очень часто попадаются 4.5, которые round все равно округляет к 4, поэтому прибавляем 0.1
        if rate:
            if rate <= 3:
                rate = 4
            # В случае подозрительно огромного количества хороших оценок заменить в условии or на and
            if count >= 3 and rate <= 3:
                rate = random.randint(4, 5)
            users = Account.objects.filter(email__in=[f'user_{c}@mail.ru' for c in range(1, int(count) + 1)])
            for user in users:
                obj, created = Rating.objects.update_or_create(user=user, product=product, defaults={'rating': rate})
                print(obj, created)
