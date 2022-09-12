from django.urls import path

from apps.reviews.views import SetReview

app_name = 'reviews'

urlpatterns = [
    path('api/set_review/', SetReview.as_view(), name='set')
]
