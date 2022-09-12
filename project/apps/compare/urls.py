from django.urls import path

from . import views

app_name = 'compare'


urlpatterns = [
    path('', views.CompareTemplateView.as_view(), name='list'),
    path('toggle/', views.ToggleCompareFormView.as_view(),
         name='compare_toggle'),
]
