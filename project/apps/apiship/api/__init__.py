"""
https://wiki.apiship.ru/pages/viewpage.action?pageId=17465357

Данный модуль делится на client, const, response и entities

Client - основной класс, через который происходит все взаимодействие с апишип
Const - константные значения
Entities - набор вспомогательных сущностей для формирования запроса
Response - классы ответов сервера на различные методы апи,
           содержат вспомогательные методы для обработки ответа

Пример создания запроса на расчет стоимости доставки:

from api import Client, Calculator, TypeDelivery, TypePickup
# передаем токен и режим взаимодействия (test и prod)
apiship = Client("token", "test")

city_from = Calculator.add_address(
    region="Ярославская область", city="Ярославль")
city_to = Calculator.add_address(city="Вологда")

weight = 2200
width = 50
height = 35
length = 60
total = 5000 # оценочная стоимость груза

calc = Calculator(city_from,
                    city_to,
                    weight,
                    width,
                    height,
                    length,
                    total,
                    pickupTypes=[TypeDelivery.FROM_POINT],
                    deliveryTypes=[TypePickup.TO_POINT])

# запрос на расчет доставки
cr = apiship.calculate(calc)

# получаем ид пунктов выдачи
point_ids = cr.get_point_ids()

# преобразуем их в строку
point_ids_str = cr.get_point_ids_str(point_ids)

# запос на получение пунктов выдачи
a = apiship.get_points(
    filter=f"id={point_ids_str}",
    limit=len(point_ids))

# получаем объект ответа
pr = PointsResponse(a.json())

# записываем тарифы в точки выдачи
points = cr.points_with_tariffs(pr)

# в итоге points - список пунктов выдачи, включающий стоимость доставки
"""

from .entities import (Calculator, CouirierCall, OrderData, OrderCost,
                       OrderAddress, OrderItems, OrderCreate)
from .client import Client
from .response import PointsResponse, CalculatorResponse
from .const import TypePickup, TypeDelivery
