from django.urls import path

from . import views

app_name = 'cart'


urlpatterns = [
    path('', views.CartTemplateView.as_view(), name='cart_detail'),
    path('add/', views.AddCartFormView.as_view(), name='cart_add'),
    path('update/', views.UpdateCartFormView.as_view(), name='cart_update'),
    path('delete/', views.DeleteCartFormView.as_view(), name='cart_delete'),
    path('repeat/<int:order_number>', views.repeat_cart, name='cart_repeat')
]
