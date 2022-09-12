from django.contrib.auth.views import (
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.urls import path

from . import views
from .views import UserPasswordChangeView

urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('confirm/user/<uidb64>/<token>/',
         views.ActivateUserView.as_view(), name='confirm-user'),
    path("login/", views.Login.as_view(), name="login"),
    path("logout/", views.logout, name="logout"),
    path(
        "password/reset/",
        views.UserPasswordResetView.as_view(),
        name="password_reset"),
    path(
        "password/reset/done/",
        PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        views.UserSetNewPassword.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password/done/",
        PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("password/change/",
         UserPasswordChangeView.as_view(),
         name="password_change"),

    path("personal/",
         views.UserUpdateView.as_view(),
         name="user-update"),
    path('confirm/new-email/<uidb64>/<token>/',
         views.ConfirmNewEmailView.as_view(), name='confirm_new_email'),
    path("personal/orders/",
         views.UserOrdersTemplateView.as_view(),
         name="personal-orders"),
    path("complete/yandex-oauth2/", views.UserUpdateView.as_view()),
    path("social/auth", views.UserAuthSocialRedirect.as_view(), name="social_auth_redirect")
]
