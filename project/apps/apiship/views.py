from django.http import JsonResponse
from django.views.generic import TemplateView

from apps.cart.models import get_cart
from .api import Calculator, PointsResponse
from .api import Client


class SandBoxView(TemplateView):
    template_name = 'apiship/sandbox.html'

    def _get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        apiship = Client("2f0b7cbf13c3619e73a3c339cfd9c6fa", "test")

        fr = Calculator.add_address(
            region="Вологодская область", city="Вологда")
        to = Calculator.add_address(
            region="Ярославская область", city="Ярославль")

        calc = Calculator(fr, to, 2200, 50, 35, 60, 5000,
                          pickupTypes=[2], deliveryTypes=[2])

        c = apiship.calculate(calc)
        a = c.json()

        massive = {}
        point_ids = []
        for delivery in a['deliveryToPoint']:
            min_tariff = None
            for tariff in delivery['tariffs']:
                if (min_tariff is None) or (
                        min_tariff is not None and tariff['deliveryCost'] < min_tariff['deliveryCost']):
                    min_tariff = tariff
            if min_tariff is not None:
                massive[delivery['providerKey']] = min_tariff
                point_ids = point_ids + min_tariff['pointIds']
                del massive[delivery['providerKey']]['pointIds']
        point_ids_str = ','.join(str(p) for p in point_ids)
        a = apiship.get_points(filter=f"id=[{point_ids_str}]", limit=len(
            point_ids))

        points = a.json()['rows']

        for point in points:
            point['info'] = massive[point['providerKey']]

        data['points'] = points

        return data

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        apiship = Client("2f0b7cbf13c3619e73a3c339cfd9c6fa", "test")

        fr = Calculator.add_address(
            region="Вологодская область", city="Вологда")
        to = Calculator.add_address(
            region="Ярославская область", city="Ярославль")

        calc = Calculator(fr, to, 2200, 50, 35, 60, 5000,
                          pickupTypes=[2], deliveryTypes=[2])

        cr = apiship.calculate(calc)
        point_ids = cr.get_point_ids()
        point_ids_str = cr.get_point_ids_str(point_ids)
        a = apiship.get_points(
            filter=f"id={point_ids_str}",
            # на тесте не работает, только на проде
            # fields='id,providerKey,paymentCard,name,lat,lng,timetable',
            limit=len(point_ids))
        pr = PointsResponse(a.json())
        points = cr.points_with_tariffs(pr)

        data['points'] = points

        return data


def get_points(request):
    city_to = request.GET.get('city')
    if not city_to:
        return JsonResponse({'success': False, 'errors': {'city_to': 'Выберите город доставки'}})

    data = {}
    apiship = Client("2f0b7cbf13c3619e73a3c339cfd9c6fa", "test")

    cart = get_cart(request)

    fr = Calculator.add_address(
        region="Ярославская область", city="Ярославль")
    to = Calculator.add_address(city=city_to)

    calc = Calculator(fr, to, 2200, 50, 35, 60, 5000,
                      pickupTypes=[2], deliveryTypes=[2])
    # посылаем запрос на расчет доставки
    c = apiship.calculate(calc)
    # получаем объект ответа
    cr = CalculatorResponse(c.json())
    # получаем ид пунктов выдачи
    point_ids = cr.get_point_ids()
    # преобразуем их в строку
    point_ids_str = cr.get_point_ids_str(point_ids)
    # запос на получение пунктов выдачи
    a = apiship.get_points(
        filter=f"id={point_ids_str}",
        # на тесте не работает, только на проде
        # fields='id,providerKey,paymentCard,name,lat,lng,timetable',
        limit=len(point_ids))
    # получаем объект ответа
    pr = PointsResponse(a.json())
    # записываем тарифы в точки выдачи
    points = cr.points_with_tariffs(pr)

    data['points'] = points

    return JsonResponse(data)
