from django.urls import path
from django.contrib.sitemaps.views import sitemap
from . import views

app_name = 'seo'


urlpatterns = [
    #path('robots.txt', views.robots, name='robots'),
    #path('sitemap.xml', sitemap, {'sitemaps': views.sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('sitemap_img.xml/', sitemap, {'sitemaps': views.image_sitemap, 'template_name': 'seo/sitemap_img.xml'},
         name='django.contrib.sitemaps.views.sitemap')
]