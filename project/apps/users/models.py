import re

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import (
    authenticate, login as django_login, logout as django_logout
)

from .managers import AccountManager
from ..catalog.models import CONTRACTORS_COUNT
from apps.domains.middleware import get_request
from apps.domains.models import Domain
from apps.catalog.models import SlugCategory


class Account(AbstractUser):
    """ Переопредленный пользователь сайта  """
    username = None
    first_name = None
    last_name = None
    name = models.CharField(_("имя"), max_length=63, blank=True, default="")
    email = models.EmailField(_("электронная почта"), unique=True, blank=True, null=True, max_length=50)
    email_new = models.EmailField(
        _("электронная почта"), blank=True, default="", max_length=50)
    phone = models.CharField(
        verbose_name=_("телефон"), blank=True, default="", max_length=34,
    )
    discount = models.PositiveSmallIntegerField(
        verbose_name="Персональная скидка",
        default=0,
        validators=[MaxValueValidator(100)],
    )
    contractor = models.PositiveSmallIntegerField('№ Контрагента', blank=True, default=None, null=True,
                                                  validators=[MaxValueValidator(CONTRACTORS_COUNT),
                                                              MinValueValidator(0)])

    history = HistoricalRecords()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = AccountManager()

    def __str__(self):
        return self.email or f'Пользователь {self.id}'

    def clean(self):
        self.phone = self.normalize_phone(self.phone) if self.phone else ''

    def save(self, *args, **kwargs):
        for slug_category in SlugCategory.objects.all():
            for domain in Domain.objects.all():
                for contractor in range(1, 4):
                    cache.delete(f'render_to_string_/{slug_category}/-{contractor}-{domain.domain}')
        return super().save(*args, **kwargs)

    @classmethod
    def normalize_phone(cls, phone):
        phone = phone or ""
        phone = re.sub(r"[^0-9]", "", phone)
        return phone

    @staticmethod
    def auth(request, user):
        django_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return user

    @staticmethod
    def auth_with_password(request, login, password):
        user = authenticate(username=login, password=password)
        if user:
            return Account.auth(request, user)
        return False

#Используется для авторизации пользователя в соц. сетях и его перенаправлении
class UserSocialSession(models.Model):
    user = models.ForeignKey(Account, editable=False, on_delete=models.CASCADE, unique=True)
    token = models.CharField(verbose_name="Токен, по которому будем искать пользователя", editable=False, max_length=500, default="")