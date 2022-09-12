from django.shortcuts import get_object_or_404, render, reverse
from django.views.generic.base import RedirectView, TemplateView
from django.template.loader import get_template
from django.http import HttpResponse

from .models import BankOrder, SberSettings
from apps.configuration.models import Settings


class PaymentRedirectView(RedirectView):
    """
    Контроль оплаты
    """
    permanent = False
    query_string = False
    # url = '/'
    # pattern_name = 'account-orders'

    def get_redirect_url(self, *args, **kwargs):
        bank_id = self.request.GET.get("orderId")
        bank_order = get_object_or_404(
            BankOrder, bank_id=bank_id)
        client = BankOrder.get_client()
        resp = client.get_order_status_extended(order_id=bank_id)
        if resp.message == 'Успешно':
            bank_order.payment_success()
            return reverse('shop:successful_pay')
        return reverse('shop:unsuccessful_pay')
