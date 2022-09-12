import pytest
import os
import django
from django.test import Client

os.environ['DJANGO_SETTINGS_MODULE'] = 'system.settings'
django.setup()

@pytest.fixture
def user(request):

    status = request.param

    if(status == "unath"):
        return unauth_user()

    elif(status == "auth"):
        return auth_user()

    elif(status == "wholesale"):
        return auth_wholesale_user()

def unauth_user():
    return Client()

def auth_user():
    client = Client()
    client.login(
        username = "testpochtarupechi@mail.ru",
        password = "testpasswordrupechi_VeryHardPASS3242442WOrd"
    )
    return client

def auth_wholesale_user():
    client = Client()
    client.login(
        username = "testpochtawholesalerupechi@mail.ru",
        password = "testpasswordwholesalerupechi_VeryHardPASS3242442WOrd"
    )
    return client 