from django.urls import path

from . import views

app_name = 'wishlist'


urlpatterns = [
    path('', views.WishlistTemplateView.as_view(), name='list'),
    path('toggle/', views.ToggleWishlistFormView.as_view(),
         name='wishlist_toggle'),
]
