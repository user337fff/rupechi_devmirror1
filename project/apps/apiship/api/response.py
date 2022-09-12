import copy
from typing import List, Dict
from abc import ABC, abstractmethod


class BaseResponse(ABC):
    """
    Абстрактный класс ответа сервера
    """
    @abstractmethod
    def __init__(self, response):
        self.response = response.json()


class PointsResponse(BaseResponse):
    """
    Ответ метода /lists/points
    """

    def __init__(self, response):
        super().__init__(self, response)
        self.points_list = self.response['rows']

    def get_points(self):
        return self.points_list


class CalculatorResponse(BaseResponse):
    """
    Ответ апи на запрос расчета стоимости доставки
    """

    def __init__(self, response):
        super().__init__(self, response)
        # разделяем доставку до двери и до пункта выдачи
        self.to_door = self.response['deliveryToDoor']
        self.to_point = self.response['deliveryToPoint']
        # атрибуты для уже вычисленных значений
        self.providers_to_door = None
        self.providers_to_point = None

    def get_min_tariff(self, tariffs: List) -> Dict:
        """
        Поиск тарифа с минимальной стоимостью из представленных
        """
        try:
            tariff = min(tariffs, key=lambda tariff: tariff['deliveryCost'])
        except ValueError:
            tariff = None
        return tariff

    def _get_deliveries(self, deliveries: List) -> Dict:
        """
        Получаем словарь ключ - идентификатор СД: значение - минимальный тариф

        ! В будущем можно сделать возможность передавать дополнительные
        ! параметры, в зависимости от которых выдавать тарифы
        ! по другим критериям, а не только по минимальной стоимости
        """
        # метод выбора тарифа из списка
        selection_method = self.get_min_tariff
        providers = {}
        for delivery in deliveries:
            tariff = selection_method(delivery['tariffs'])
            if tariff is not None:
                providers[delivery['providerKey']] = tariff
        return providers

    def get_deliveries_to_door(self):
        """
        Получение доставок до двери с минимальным тарифом
        """
        if self.providers_to_door is None:
            self.providers_to_door = self._get_deliveries(self.to_door)
        return self.providers_to_door

    def get_deliveries_to_point(self):
        """
        Получение доставок до склада с минимальным тарифом
        """
        if self.providers_to_point is None:
            self.providers_to_point = self._get_deliveries(self.to_point)
        return self.providers_to_point

    def get_point_ids(self):
        """
        Получение ид точек выдачи
        """
        deliveries = self.get_deliveries_to_point()
        point_ids = []
        for delivery in deliveries.values():
            point_ids = point_ids + delivery['pointIds']
            del delivery['pointIds']
        return point_ids

    def get_point_ids_str(self, point_ids=None, brackets=True):
        if point_ids is None:
            point_ids = self.get_point_ids()
        # преобразование через join, т.к. ид должны быть без пробелов
        # как при обычном str(list)
        points_str = ','.join(str(p) for p in point_ids)
        if brackets:
            points_str = f'[{points_str}]'
        return points_str

    def points_with_tariffs(self, points_response: PointsResponse):
        """
        Получение точек выдачи с тарифами

        points_response - ответ от апи метода /lists/points

        """

        points = points_response.get_points()
        deliveries_to_point = copy.deepcopy(self.get_deliveries_to_point())
        for point in points:
            point['info'] = deliveries_to_point[point['providerKey']]
        return points
