"""
Django settings for place_shop project.

Generated by 'django-admin startproject' using Django 3.0.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import traceback

from django.utils.translation import ugettext_lazy as _
from system.db import db

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'l$m4i79y^4%(xz%r-j0)=y%)*(pp82-@=gm16!e3yoftagb*cf'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
APPEND_SLASH = True

ALLOWED_HOSTS = [
    "*",
]
CSRF_TRUSTED_ORIGINS = ['www.devmirror1.srv-rupechi-test1.place-start.ru']
# Application definition

INSTALLED_APPS = [
    "apps.jet_fix",
    "jet.dashboard",
    "jet",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    'debug_toolbar',
    'django_redis',
    "sorl.thumbnail",
    "ckeditor",
    "ckeditor_uploader",
    "mptt",
    "adminsortable2",
    "simple_history",
    "colorfield",
    'social_django',
]

CUSTOM_APPS = [
    "apps.users",
    "apps.commons",
    "apps.nav",
    "apps.catalog",
    "apps.product_options",
    "apps.shop",
    'apps.stores',
    "apps.cart",
    "apps.apiship",
    "apps.feedback",
    "apps.pages",
    "apps.configuration",
    "apps.sber_acquiring",
    "apps.compare",
    "apps.wishlist",
    "apps.seo",
    "apps.bonus",
    "apps.exchange1c",
    "apps.komtet",
    "apps.domains",
    "apps.analytics",
    "apps.template_editor",
    "apps.reviews",
]

INSTALLED_APPS += CUSTOM_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # debug
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # added
    "django.middleware.locale.LocaleMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "apps.domains.middleware.CurrentDomainMiddleware",
    'apps.domains.middleware.GlobalRequest',
]

#for debug toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    '95.56.181.13'
]

def strip_sensitive_data(event, hint):

    try:
        print("Ошибка")
        for value in event["exception"]["values"]:
            print(value["type"])
            if(value["type"] == "OSError"):
                print("Ошибка OSError")
                return None

        # modify event here
        return event
    except:
        traceback.print_exc()
        return event

def traces_sampler(sampling_context):
    return 1

sentry_sdk.init(
    dsn="https://a3e606e55474491a85fb15a30b124ba2@o1323260.ingest.sentry.io/6580865",
    integrations=[
        DjangoIntegration(),
    ],
    traces_sampler=traces_sampler,
    before_send=strip_sensitive_data,
)

def show_toolbar(request):
    return False

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
}

ROOT_URLCONF = "system.urls"

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # custom context processors
                "apps.cart.context_processors.cart",
                "apps.configuration.context_processors.context_settings",
                "apps.nav.context_processors.context_nav",
                "apps.catalog.context_processors.context_catalog",
                "apps.wishlist.context_processors.wishlist",
                "apps.compare.context_processors.compare",
                'apps.domains.context_processors.context_domains',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = "system.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = db

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_VALID_MODULE = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"{AUTH_VALID_MODULE}.UserAttributeSimilarityValidator"},
    {"NAME": f"{AUTH_VALID_MODULE}.MinimumLengthValidator"},
    {"NAME": f"{AUTH_VALID_MODULE}.CommonPasswordValidator"},
    {"NAME": f"{AUTH_VALID_MODULE}.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.Account"
LOGIN_REDIRECT_URL = 'user-update'

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "ru"

USE_I18N = True

USE_L10N = False
DECIMAL_SEPARATOR = '.'

USE_TZ = True
TIME_ZONE = 'Europe/Moscow'

LANGUAGES = (
    ('ru', _('Russian')),
    ('en', _('English')),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

# STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATIC_URL = "/static/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static"),
                    os.path.join(BASE_DIR, "src")]

MEDIA_ROOT = os.path.join(BASE_DIR, "../media")

MEDIA_URL = "/media/"

FILE_UPLOAD_MAX_MEMORY_SIZE = 200000000
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_HANDLERS = [ 'django.core.files.uploadhandler.MemoryFileUploadHandler', ]
DATA_UPLOAD_MAX_MEMORY_SIZE = 200000000

# Email settings
EMAIL_HOST = "m1.system.place-start.ru"
EMAIL_PORT = 25
EMAIL_HOST_USER = None
EMAIL_HOST_PASSWORD = None
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = "rupechi.ru@drv6.ps"

# Ckeditor
CKEDITOR_UPLOAD_PATH = "uploads/"

CKEDITOR_CONFIGS = {
    "default": {
        "removePlugins": "stylesheetparser",
        'allowedContent': True,
        'toolbar_Full': [
            ['Styles', 'Format', 'Bold', 'Italic', 'Underline', 'Strike',
             'Subscript', 'Superscript', '-', 'RemoveFormat'],
            ['Image', 'Flash', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['Smiley', 'sourcearea', 'SpecialChar'],
            ['Link', 'Unlink', 'Anchor'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-',
             'Blockquote', 'CreateDiv', '-', 'JustifyLeft', 'JustifyCenter',
             'JustifyRight', 'JustifyBlock', '-', 'BidiLtr', 'BidiRtl',
             'Language'],
            ['Source', '-', 'Save', 'NewPage', 'Preview', 'Print', '-',
             'Templates'],
            ['Cut', 'Copy', 'Paste', 'PasteText',
             'PasteFromWord', '-', 'Undo', 'Redo'],
            ['Find', 'Replace', '-', 'SelectAll', '-', 'Scayt'],
            ['Maximize', 'ShowBlocks']
        ],
    }
}

DATETIME_FORMAT = 'd.m.Y H:i:s'

# Jet settings
JET_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'

JET_THEMES = [
    {
        'theme': 'default',  # theme folder name
        'color': '#47bac1',  # color of the theme's button in user menu
        'title': 'Default'  # theme title
    },
    {
        'theme': 'green',
        'color': '#44b78b',
        'title': 'Green'
    },
    {
        'theme': 'light-green',
        'color': '#2faa60',
        'title': 'Light Green'
    },
    {
        'theme': 'light-violet',
        'color': '#a464c4',
        'title': 'Light Violet'
    },
    {
        'theme': 'light-blue',
        'color': '#5EADDE',
        'title': 'Light Blue'
    },
    {
        'theme': 'light-gray',
        'color': '#222',
        'title': 'Light Gray'
    }
]

# нужно для корректной работы jet
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Убрать двухуровенове меню
# JET_SIDE_MENU_COMPACT = True

JET_SIDE_MENU_ITEMS = [
    {
        'app_label': 'catalog',
        'permissions': ['catalog.change_product'],
        'items': [
            {'name': 'product'},
            {'name': 'brand'},
            {'name': 'alias'},
            {'name': 'catalog'},
            {'name': 'category'},
            {'name': 'calc'},
            {'name': 'productattribute'},
            {'name': 'categoryattribute'},

        ]
    },
    {
        'app_label': 'reviews',
        'permissions': ['reviews.change_review'],
        'items': [
            {'name': 'review'},
        ]
    },
    {'app_label': 'shop',
     'permissions': ['shop.change_order'],
     'items': [
         {'name': 'order', },
         {'name': 'endpoints', },
     ]},
    {'app_label': 'stores',
     'permissions': ['stores.change_store'],
     'items': [
         {'name': 'store', },
     ]},
    {'app_label': 'cart',
     'permissions': ['cart.change_cart'],
     'items': [
         {'name': 'cart'},
     ]},
    {'app_label': 'pages',
     'permissions': ['pages.change_page'],
     'items': [
         {'name': 'page'},
     ]},
    {'app_label': 'feedback',
     'permissions': ['feedback.change_feedback'],
     'items': [
         {'name': 'recipient'},
         {'name': 'mail'},
     ]},
    {'app_label': 'nav',
     'permissions': ['nav.change_headermenuitem'],
     'items': [
         {'name': 'headermenuitem'},
         {'name': 'footermenuitem'},
         {'name': 'sidebarmenuitem'},
         {'name': 'catalogmenuitem'},
     ]},
    {'app_label': 'apiship',
     'permissions': ['apiship.change_ordershipping'],
     'items': [
         {'name': 'ordershipping'},
     ]},
    {'app_label': 'configuration',
     'permissions': ['configuration.change_settings'],
     'items': [
         {'name': 'settings'},
         {'name': 'delivery'},
         {'name': 'payment'},
         {'name': 'indexslide'},
     ]},
    {'app_label': 'sber_acquiring',
     'permissions': ['sbersettings.change_sbersettings'],
     'items': [
         {'name': 'sbersettings'},
     ]},
    {'app_label': 'komtet',
     'permissions': ['komtet.change_komtetsettings'],
     'items': [
         {'name': 'komtetsettings'},
     ]},
    {'app_label': 'bonus',
     'permissions': ['bonus.change_bonussettings'],
     'items': [
         {'name': 'bonussettings'},
         {'name': 'bonusaccount'},
         {'name': 'action'},
     ]},
    {'app_label': 'exchange1c',
     'permissions': ['exchange1c.change_settings'],
     'items': [
         {'name': 'settings'},
     ]},
    {'app_label': 'domains',
     'permissions': ['domains.change_domain'],
     'items': [
         {'name': 'domains.domain'},
     ]},
    {'app_label': 'users', 'items': [
        {'name': 'users.account'},
        {'name': 'auth.group'},
    ]},

]

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/',
        'TIMEOUT': 10 * 60,  # 10 минут
        'KEY_PREFIX': 'rupechi-devmirror1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
# sorl-thumbnail
THUMBNAIL_PRESERVE_FORMAT = True
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_KEY_PREFIX = 'rupechi-devmirror1'

# настройки базового домена

DEFAULT_DOMAIN = 'place-shop.ru'
DEFAULT_DOMAIN_DISPLAY = 'Интернет-магазин'

# SOCIAL
SOCIAL_AUTH_POSTGRES_JSONFIELD = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_core.backends.vk.VKOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.yandex.YandexOAuth2',
    'social_core.backends.yandex.YandexOpenId',
)

SOCIAL_AUTH_URL_NAMESPACE = 'social'

SOCIAL_AUTH_FACEBOOK_API_VERSION = '10.0'
SOCIAL_AUTH_FACEBOOK_SECRET = '2a0ad70f8a3b070f22a1c609ed53867a'
SOCIAL_AUTH_FACEBOOK_KEY = '303309407826675'
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]

SOCIAL_AUTH_VK_OAUTH2_SECRET = '9Xx3AMWccXUWI8DY9gc8'
SOCIAL_AUTH_VK_OAUTH2_KEY = '8192877'
SOCIAL_AUTH_VK_OAUTH2_SCOPE = ['email']

#SOCIAL_AUTH_YANDEX_OAUTH2_KEY = 'e3cf147f49bb548648080db2bda70df40'
#SOCIAL_AUTH_YANDEX_OAUTH2_SECRET = '14fd193494c54535b7e854b6abff9495'

SOCIAL_AUTH_YANDEX_OAUTH2_KEY = '23969468bb5b41c49511ba6f3c98e337'
SOCIAL_AUTH_YANDEX_OAUTH2_SECRET = 'f6bd79d3216c48a2976cafb5ec161f1c'

SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'https://www.devmirror1.srv-rupechi-test1.place-start.ru/users/social/auth?action=3'

YANDEX_APP_ID = SOCIAL_AUTH_YANDEX_OAUTH2_KEY
YANDEX_API_SECRET = SOCIAL_AUTH_YANDEX_OAUTH2_SECRET

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
        'handlers': {
            # Send all messages to console
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
        # This is the "catch all" logger
        '': {
            'handlers': ['console',],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
