from .const import OrderStatus


class BaseResponse:
    """
    Ответ апи сбербанка
    """
    SUCCESS_CODE = 0

    success = False
    message = None

    data = None

    def __init__(self, response):
        self.response = response
        if response.status_code == 200:
            self.data = response.json()
            self._init_status()

    def _init_status(self):
        if self.data is not None and self.data.get('errorCode', 0) == 0:
            self.success = True
        elif self.data:
            self.message = self.data.get('errorMessage')

    def __getattr__(self, attr):
        if self.data and attr in self.data:
            return self.data[attr]
        raise AttributeError(
            f"{type(self).__name__} object has no attribute '{attr}'")


class OrderRegisterResponse(BaseResponse):
    """
    Ответ на создание заказа
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def order_number(self):
        return self.orderId

    @property
    def url(self):
        return self.formUrl


class OrderStatusResponse(BaseResponse):
    """
    Ответ на получение статуса заказа
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def is_valid(self):
        if (self.success and
                self.orderStatus in [OrderStatus.SUCCESS, OrderStatus.HOLD]):
            return True
        return False
