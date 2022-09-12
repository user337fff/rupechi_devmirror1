import threading

from apps.domains.models import Domain
from django.apps import apps
from django.utils.deprecation import MiddlewareMixin


class CurrentDomainMiddleware(MiddlewareMixin):
    """
    Устанавливаем домен в объект реквеста
    """
    def process_request(self, request):
        request.domain = Domain.objects.get(domain="www.rupechi.ru")


request_object = threading.local()


class GlobalRequest(MiddlewareMixin):

    def process_request(self, request):
        global request_object
        request_object.request = request


def get_request():
    if hasattr(request_object, 'request'):
        return request_object.request
    return FakeDomain()


class FakeDomain:
    # если нужно провести миграцию в доменах, необходимо установить domain = None
    domain = None
    GET = {}
    POST = {}
    path = ''
    user = None

    def __init__(self):
        super(FakeDomain, self).__init__()
        Account = apps.get_model('users', 'Account')
        self.user = Account.objects.filter(is_superuser=True).first()
        try:
            self.domain = Domain.objects.first()
        except Exception:
            self.domain = None
