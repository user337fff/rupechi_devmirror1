from django.urls import path

from . import views

app_name = 'apiship'


urlpatterns = [
    path('', views.SandBoxView.as_view(), name='sandbox'),
    path('points/', views.get_points, name='points'),
]
