from django.urls import path, re_path
from .views import Exchange1cView, orders_xml_debug
from django.http import HttpResponse

urlpatterns = [

    path("ok.py/", Exchange1cView.as_view(), name='1c_exchange'),
    path('ok<str:postfix>.py/', Exchange1cView.as_view(), name='1c_exchange'),
    
    #re_path(r'^1c_exchange.py/$', lambda request: HttpResponse("Bye"), name='1c_exchange'),
    #path('1c_exchange<str:postfix>.py/', Exchange1cView.as_view(), name='1c_exchange_prefix'),

    #path('1c_orders.xml', orders_xml_debug, name='1c_orders_debug'),
    #path('1c_orders<str:postfix>.xml', orders_xml_debug, name='1c_orders_debug'),
]
