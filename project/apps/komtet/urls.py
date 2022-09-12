from django.urls import path

from . import views

app_name = 'komtet'


urlpatterns = [
    path('success/', views.KomtetSuccsessView.as_view(), name='success'),
    path('failure/', views.KomtetFailureView.as_view(), name='failure')
]
