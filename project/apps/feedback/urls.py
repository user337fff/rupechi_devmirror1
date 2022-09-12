from django.urls import path
from apps.feedback.views import GiveCoupon, CalcMounting, SubscribeView, CoopView, OneClickView, CheaperView, InStockView

app_name = 'feedback'

urlpatterns = [
    path('coupon/', GiveCoupon.as_view(), name='coupon'),
    path('mounting/', CalcMounting.as_view(), name='mounting'),
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('coop/', CoopView.as_view(), name='coop'),
    path('oneclick/', OneClickView.as_view(), name='oneclick'),
    path('cheaper/', CheaperView.as_view(), name='cheaper'),
    path('in-stock/', InStockView.as_view(), name='in_stock')
]