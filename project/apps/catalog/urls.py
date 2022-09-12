from django.conf.urls import url
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from . import views


urlpatterns = [
    url(r"^photoproducts/(?P<slug>.*)$", views.UnloadingPhotoView.as_view()),
    path('catalog/search-products/', views.SearchProductsListView.as_view(), name='search'),
    path('catalog/', views.CatalogTemplateView.as_view(), name='catalog'),
    path('rasprodazha/', views.SaleView.as_view(), name='sale'),
    path('rasprodazha/f/(?P<attrs>.*))/', views.SaleView.as_view()),
    path('proizvoditeli/', views.BrandsView.as_view(), name='brands'),
    path('search/', views.SearchPageView.as_view(), name='search-page'),
    path('search/f/(?P<attrs>.*)/', views.SearchPageView.as_view()),
    path('api/set_rating/', views.SetRating.as_view(), name='set_rating'),
    re_path(r'proizvoditeli/(?P<slug>.*)/', views.BrandDetail.as_view(), name='brand'),
    # path('catalog/category-products/', views.CategoryProductsListView.as_view(), name='category_products'),
    re_path(r'catalog/(?P<slug>.*)/', views.CategoryDetailView.as_view(), name='category'),
    re_path(r'product/(?P<slug>.*)/$', views.ProductDetail.as_view(), name='product'),
    re_path(r'product/(?P<slug>.*[^\/])$', views.RedirectEndSlash),
    re_path(r'category_products/(?P<type>[^\/]+)/(?P<slug>.*)/f/.{0,800}',
            views.CategoryDetailSEF.as_view(), name='category_sef'),

]
