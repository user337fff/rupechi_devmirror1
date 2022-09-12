from django.urls import path
from django.views.generic.base import TemplateView
from django.shortcuts import render

from . import views

app_name = 'sber'


urlpatterns = [
    path('valid/', views.PaymentRedirectView.as_view(), name='sber_payment')
]
