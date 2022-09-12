from apps.pages import views
from django.urls import path, re_path

app_name = 'pages'

urlpatterns = [
    path('success_pay/', views.TestPage.as_view(), name='success'),
    path('rss/', views.UsefulPagesFeed(), name='page_feed'),
    path('headings/<slug>/', views.HeadingDetail.as_view(), name='heading_detail'),
    path('address/', views.AddressView.as_view(), name='address'),
    re_path(r'(?P<slug>.*)/', views.get_new_catalog, name='page_detail'),
    path('<heading_slug>/<slug>/', views.PostDetail.as_view(), name='post_detail'),
    # path('<slug>/', views.PageDetail.as_view(), name='page_detail'),
]
