from django.urls import path
from django.views.generic.base import TemplateView

from . import views

app_name = 'shop'


urlpatterns = [
    path('order/', views.OrderCreateView.as_view(), name='order'),
    path('order-pay/<int:order_id>', views.OrderPay.as_view(), name='order-pay'),
    path('payment/', TemplateView.as_view(template_name='sber_acquiring/successful_payment.html'), name='successful_pay'),
    #path('not_payment/', TemplateView.as_view(template_name='sber_acquiring/unsuccessful_payment.html'),
    #    name='unsuccessful_pay')
    path('not_payment/', views.NotPaymentView.as_view(), name='unsuccessful_pay')
]
