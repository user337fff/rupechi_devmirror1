import uuid
from xml.dom import minidom
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement
from django.http import HttpResponse, FileResponse
from django.utils import timezone

from apps.shop.models import Order, OrderItem, EndPoint
from apps.sber_acquiring.models import BankOrder
from apps.configuration.models import Delivery
from .models import Settings


def prettify(elem):
    rough_string = ET.tostring(elem, u'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='   ')


class OrderXml(Order):
    """Прокси-модель заказа для генерации в xml"""
    settings = None
    xml = None

    class Meta:
        proxy = True

    def to_xml(self, settings):
        self.settings = settings
        self.set_order()
        return self.xml

    def set_order(self):
        self.xml = Element('Документ')
        # префикс к ид заказа
        online_pay = False
        if self.settings.order_prefix:
            order_id = f'{self.settings.order_prefix}{self.pk}'
        else:
            order_id = str(self.pk)
            if self.status in ['awaiting', 'paid']:
                online_pay = True
        SubElement(self.xml, 'Ид').text = order_id
        SubElement(self.xml, 'Номер').text = order_id
        SubElement(self.xml, 'Дата').text = str(self.created_at.date())
        SubElement(self.xml, 'ХозОперация').text = 'Заказ товара'
        SubElement(self.xml, 'Роль').text = 'Продавец'
        self.set_currency()
        SubElement(self.xml, 'Сумма').text = str(self.total)
        SubElement(self.xml, 'ОнлайнОплата').text = 'Да' if online_pay else 'Нет'
        if online_pay:
            SubElement(self.xml, 'СтатусОплаты').text = 'Оплачен' if self.paid else 'Ожидает оплаты'
            if self.paid:
                self.card_number = BankOrder.objects.get(order=self).card_number
                SubElement(self.xml, 'НомерКарты').text = str(self.card_number)
        delivery_filter = Delivery.objects.filter(title='Заказ с самовывозом')
        if self.delivery in delivery_filter:
            delivery_comment = self.store
            delivery_type = self.delivery
        else:
            delivery_comment = f'{self.city}, {self.address}'
            delivery_type = self.delivery
        if not self.email:
            comment = u'ЗаказВ1Клик'
        else:
            comment = self.comment
        if comment == None:
            comment = u'НЕ УКАЗАН'
        SubElement(self.xml, 'Комментарий').text = ' / '.join(
            [
                str(comment),
                str(delivery_type),
                str(delivery_comment)
            ]
        )
        created_at = self.created_at.time().strftime('%H:%M:%S')
        SubElement(self.xml, 'Время').text = created_at
        self.set_contragents()
        self.set_items()

        self.set_requisites()

    def set_contragents(self):
        contragents = SubElement(self.xml, 'Контрагенты')
        customer = SubElement(contragents, 'Контрагент')
        if self.user:
            user_id = str(self.user_id)
        else:
            user_id = str(uuid.uuid4())
        SubElement(customer, 'Ид').text = user_id
        SubElement(customer, 'Наименование').text = self.name
        # SubElement(customer, 'ОфициальноеНаименование').text = self.name
        SubElement(customer, 'Роль').text = "Покупатель"

        contact = SubElement(customer, 'Контакты')
        contact_info = SubElement(contact, 'Контакт')
        SubElement(contact_info, 'Тип').text = 'Почта'
        SubElement(contact_info, 'Значение').text = self.email

        contact_info = SubElement(contact, 'Контакт')
        SubElement(contact_info, 'Тип').text = 'Телефон рабочий'
        SubElement(contact_info, 'Значение').text = self.phone

        representatives = SubElement(customer, 'Представители')

        representative = SubElement(representatives, 'Представитель')
        SubElement(representative, 'Отношение').text = 'Контактное лицо'
        SubElement(representative, 'Наименование').text = self.name

        # if getattr(self, 'inn', False):
        #     customer = SubElement(customer, 'РеквизитыЮрЛица')
        #     SubElement(customer, 'ИНН').text = self.inn
        #     SubElement(customer, 'КПП').text = self.kpp
        #     SubElement(
        #         customer, 'ОфициальноеНаименование').text = self.company
        # else:
        #     customer = SubElement(customer, 'РеквизитыФизЛица')
        #     SubElement(customer, 'ПолноеНаименование').text = self.name

    def set_currency(self):
        SubElement(self.xml, 'Валюта').text = "RUB"
        SubElement(self.xml, 'Курс').text = '1'

    def set_items(self):
        xml_items = SubElement(self.xml, 'Товары')
        for item in OrderItemXml.objects.filter(order=self):
            xml_items.append(item.to_xml(self.settings))

    def set_requisites(self):
        xml_props = SubElement(self.xml, 'ЗначенияРеквизитов')
        xml_prop = SubElement(xml_props, 'ЗначениеРеквизита')
        SubElement(xml_prop, 'Наименование').text = 'Дата изменения статуса'
        SubElement(xml_prop, 'Значение').text = self.updated_at.strftime(
            '%Y-%m-%d %H:%M:%S')
        xml_prop = SubElement(xml_props, 'ЗначениеРеквизита')
        SubElement(xml_prop, 'Наименование').text = 'Статус заказа'
        SubElement(xml_prop, 'Значение').text = self.get_status_display()


class OrderItemXml(OrderItem):
    """Прокси-модель элемента заказа для генерации в xml"""
    class Meta:
        proxy = True

    def set_unit(self):
        """Устнавливаем единицы измерения"""
        base_in = SubElement(self.xml, 'БазоваяЕдиница')
        base_in.text = "шт"
        base_in.set('Код', '796')
        base_in.set('МеждународноеСокращение', 'PCE')
        base_in.set('НаименованиеПолное', 'Штука')

    def set_price(self):
        SubElement(self.xml, 'ЦенаЗаЕдиницу').text = str(self.price)
        SubElement(self.xml, 'Количество').text = str(self.quantity)
        SubElement(self.xml, 'Сумма').text = str(self.total)

    def set_requisites(self):
        """Устанавливаем значения реквизитов"""
        xml_props = SubElement(self.xml, 'ЗначенияРеквизитов')

        xml_prop = SubElement(xml_props, 'ЗначениеРеквизита')
        SubElement(
            xml_prop, 'Наименование').text = 'ВидНоменклатуры'
        SubElement(xml_prop, 'Значение').text = 'Товар'

        xml_prop = SubElement(xml_props, 'ЗначениеРеквизита')
        SubElement(
            xml_prop, 'Наименование').text = 'ТипНоменклатуры'
        SubElement(xml_prop, 'Значение').text = 'Товар'

    def set_item(self):
        self.xml = Element('Товар')
        if self.product.id_1c:
            product_id = str(self.product.id_1c)
        else:
            product_id = str(self.product.pk)
        SubElement(self.xml, 'Ид').text = product_id
        SubElement(self.xml, 'Наименование').text = self.product.title
        self.set_unit()
        self.set_price()
        self.set_requisites()

    def to_xml(self, settings):
        self.settings = settings
        self.set_item()
        return self.xml


class OrdersXmlGenerator:
    """
    Генератор заказов в xml для экспорта 1с
    queryset - базовый набор заказов для экспорта
    debug - для генерации заказов независимо от ранней выгрузки
    DEBUG_ORDERS_COUNT - количество отображаемых заказов при включенном дебаге
    """
    queryset = OrderXml.objects.all()

    debug = True
    DEBUG_ORDERS_COUNT = 20

    def __init__(self, settings=None, debug=True, postfix=''):
        if settings is None:
            self.settings = Settings.load()
        else:
            self.settings = settings

        self.debug = debug
        self.postfix = postfix
        self.set_queryset()

    def set_queryset(self):

        if not self.debug:
            # невыгруженные заказы
            #endpoint = EndPoint.objects.filter(slug=self.postfix).first()
            self.queryset = self.queryset.filter(
                status_export__in=[Order.EXCHANGE_STATUS_NOT, Order.EXCHANGE_STATUS_PROCESSING]
            )
            #if endpoint:
            #    self.queryset = endpoint.filter(self.queryset)
            #else:
            #    self.queryset = self.queryset.none()

    def _settings_status_gte(self):
        """Выгружать заказы начиная с указанного статуса"""
        exclude_statuses = []
        for status, _ in Order.STATUS_CHOICES:
            if status != self.settings.orders_status_gte:
                exclude_statuses.append(status)
            else:
                break
        if exclude_statuses:
            self.queryset = self.queryset.exclude(status__in=exclude_statuses)

    def apply_settings(self):
        """Применение настроек"""
        # только оплаченные заказы
        if self.settings.only_paid_orders:
            self.queryset = self.queryset.filter(paid=True)
        # только заказы начиная с указанного статуса
        self._settings_status_gte()

        if self.debug:
            self.queryset = self.queryset[:self.DEBUG_ORDERS_COUNT]

    @classmethod
    def generate_sales(cls, settings=None, **kwargs):
        return cls(settings, **kwargs).to_xml()

    def to_xml(self):
        """Экспорт заказов в xml"""
        self.apply_settings()
        self.root = Element('КоммерческаяИнформация')
        self.root.set("xmlns", "urn:1C.ru:commerceml_2")
        self.root.set("xmlns:xs", "http://www.w3.org/2001/XMLSchema")
        self.root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        self.root.set('ВерсияСхемы', '2.03')
        self.root.set('ДатаФормирования', timezone.now().date().isoformat())
        self.orders = self.queryset

        for order in self.orders:
            self.root.append(order.to_xml(self.settings))

        # root = prettify(self.root)
        root = '<?xml version="1.0" encoding="utf-8"?>\n' + prettify(self.root)
        root = root.replace('<?xml version="1.0" ?>\n', "")
        response = HttpResponse(content_type='text/xml')
        response.write(root.encode('UTF-8'))
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Max-Age"] = "1000"
        response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type"

        # статус экспорта заказов "в процесссе"
        if not self.debug:
            for order in self.orders:
                order.status_export = Order.EXCHANGE_STATUS_PROCESSING
                order.save(update_fields=['status_export'])

        # tree = ET.ElementTree(self.root)
        # import io
        # file = io.BytesIO()
        # tree.write(file)
        # return file
        return response
