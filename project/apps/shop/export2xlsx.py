from apps.commons.export import ExportLimiter, ExportXlsx
from .models import Order, OrderItem


class ExportLimiterOrder(ExportLimiter):
    PERIOD_REPEAT = 60

    @classmethod
    def export(cls, user):
        return super().export(user, ExportXlsxOrder().export2bytes)


class ExportXlsxOrder(ExportXlsx):
    # номера колонок
    ID = 0
    TOTAL = 1
    CREATED_AT = 2
    PRODUCT = 3
    PRICE = 4
    QUANTITY = 5
    TOTAL_ITEM = 6
    SHIPPING = 7
    PAYMENT = 8
    COMMENT = 9
    PERSONAL_DATA = 10

    folder = "orders/xlsx/"
    file_prefix = "orders"

    def __init__(self, queryset=None):
        self.queryset = queryset

    def _get_headline(self) -> list:
        headline = [
            "№ заказа", "Сумма", "Дата", "Товар", "Цена", "Количество", "Сумма",
            "Доставка", "Комментарий", "Личные данные"]
        return headline

    def get_queryset(self):
        if self.queryset is None:
            return Order.objects.all()

    def get_queryset_items(self):
        return OrderItem.objects.select_related("product", "order").filter(
            order__in=self.get_queryset()).order_by("-id")

    def _export(self):
        worksheet = self.workbook.add_worksheet()
        # ширина колонки
        # № заказа
        worksheet.set_column(self.ID, self.ID, 5)
        # сумма
        worksheet.set_column(self.TOTAL, self.TOTAL, 10)
        # дата
        worksheet.set_column(self.CREATED_AT, self.CREATED_AT, 15)
        # товар
        worksheet.set_column(self.PRODUCT, self.PRODUCT, 30)
        # цена
        worksheet.set_column(self.PRICE, self.PRICE, 5)
        # количесвто
        worksheet.set_column(self.QUANTITY, self.QUANTITY, 5)
        # сумма
        worksheet.set_column(self.TOTAL_ITEM, self.TOTAL_ITEM, 8)

        # Заголовок таблицы
        headline = self._get_headline()
        for col, item in enumerate(headline):
            worksheet.write(0, col, item)

        order_items = self.get_queryset_items()
        count_items = len(order_items)
        # проходим по элементам заказов,
        # запоминаем предыдущий заказ и номер первой строки в предыдущем заказе
        prev = None
        start_row_order = 1
        for row, item in enumerate(order_items, 1):
            # если заказ элемента не равен предыдущему
            # то объединяем ячейки начиная от первого элемента прошлого заказа
            # и заканчивая последним
            is_last_row = (row == count_items)
            if not item.order == prev or is_last_row:
                if prev is not None:
                    finish_row_order = count_items if is_last_row else row-1
                    worksheet.merge_range(
                        start_row_order,
                        self.ID,
                        finish_row_order,
                        self.ID, item.order.id)
                    worksheet.merge_range(
                        start_row_order,
                        self.TOTAL,
                        finish_row_order,
                        self.TOTAL, item.order.get_total())
                    worksheet.merge_range(
                        start_row_order,
                        self.CREATED_AT,
                        finish_row_order,
                        self.CREATED_AT,
                        item.order.created_at.strftime("%H:%M %d-%m-%y"))
                    start_row_order = row
                prev = item.order

            worksheet.write(row, self.PRODUCT, item.product.title)
            worksheet.write(row, self.PRICE, item.price)
            worksheet.write(row, self.QUANTITY, item.quantity)
            worksheet.write(row, self.TOTAL_ITEM, item.total)

        self.workbook.close()
        return self.result
