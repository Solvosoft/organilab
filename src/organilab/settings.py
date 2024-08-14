from django.urls import reverse_lazy
import os
import sys

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY',
                       '8sko4lo%ca!0e^-i%7@6hnzxmc7l0^m040n%jy99z_e8cvmta)')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'
GLITCHTIP_DSN=os.getenv("GLITCHTIP_DSN", None)
if not DEBUG and GLITCHTIP_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=GLITCHTIP_DSN,
        integrations=[DjangoIntegration()],
        auto_session_tracking=False,
        traces_sample_rate=0
    )

CSRF_TRUSTED_SCHEME=os.getenv('CSRF_TRUSTED_SCHEME', 'https')
if os.getenv('ALLOWED_HOSTS', ''):
    ALLOWED_HOSTS = [c for c in os.getenv('ALLOWED_HOSTS', '').split(',')]
    CSRF_TRUSTED_ORIGINS = [CSRF_TRUSTED_SCHEME+"://"+c for c in os.getenv('ALLOWED_HOSTS', '').split(',')]
else:
    ALLOWED_HOSTS = []

ADMINS = [('Solvo', 'sitio@solvosoft.com'),]
# Application definition

SITE_ID = 1
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'auth_and_perms',  # needs to start after gentelella
    'presentation',
    'django_ajax',
    'laboratory',
    'authentication',
    'academic',
    "djreservation",
    "celery",
    'location_field',
    'rest_framework',
    'rest_framework.authtoken',
    'captcha',
    'msds',
    'sga',
    'async_notifications',
    'django_celery_results',
    'risk_management',
    'markitup',
    'djgentelella',
    'djgentelella.blog',
    'djgentelella.chunked_upload',
    'api.apps.ApiConfig',
    'reservations_management',
    'django_celery_beat',
    'paypal.standard.ipn',
    'derb',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'report'
]



IMAGE_CROPPING_JQUERY_URL = None
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'auth_and_perms.middleware.ProfileLanguageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'auth_and_perms.middleware.ImpostorMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'djreservation.middleware.ReservationMiddleware',
    'authentication.middleware.ProfileMiddleware'
]

X_FRAME_OPTIONS = "SAMEORIGIN"
ROOT_URLCONF = 'organilab.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

WSGI_APPLICATION = 'organilab.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DBNAME', 'organilab'),
        'USER': os.getenv('DBUSER', 'organilab_user'),
        'PASSWORD': os.getenv('DBPASSWORD', '0rg4n1l4b'),
        'HOST': os.getenv('DBHOST', '127.0.0.1'),
        'PORT': os.getenv('DBPORT', '5432'),
        'TEST': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DBNAME', 'organilab_test'),
            'USER': os.getenv('DBUSER', 'organilab_user'),
            'PASSWORD': os.getenv('DBPASSWORD', '0rg4n1l4b'),
            'HOST': os.getenv('DBHOST', '127.0.0.1'),
            'PORT': os.getenv('DBPORT', '5432'),
        },
    }
}

READONLY_DATABASE = os.getenv('READONLY_DATABASE', 'default')

# TEST - DJANGO

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
   # 'auth_and_perms.authBackend.BCCRBackend',  # Digital signature
)

# END TEST

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOCALE_PATHS = [
    BASE_DIR / 'locale/',
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'es'
LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
]

TIME_ZONE = 'America/Costa_Rica'

USE_I18N = True

USE_L10N = False

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = os.getenv('STATIC_ROOT', '/run/static/')

MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = os.getenv('MEDIA_ROOT',  str(BASE_DIR.parent/ 'media/'))
TINYMCE_UPLOAD_PATH=Path(MEDIA_ROOT) / 'editorupload/'

FIXTURE_DIRS = os.getenv('FIXTURE_DIRS',  str(BASE_DIR.parent/ 'fixtures/') ).split(',')

DOCS_SOURCE_DIR = os.getenv('DOCS_STATIC_DIR',  str(BASE_DIR.parent / 'docs/source/'))

# Authentication settings
LOGIN_REDIRECT_URL = reverse_lazy('auth_and_perms:select_organization_by_user')
LOGOUT_REDIRECT_URL = reverse_lazy('index')

# Email development settings
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', "sitio@organilab.org")
#EMAIL_HOST = "localhost"
#EMAIL_PORT = "1025"

#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower()  == 'true'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')  # mail service smtp
EMAIL_PORT = os.getenv('EMAIL_PORT', '1025')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', None)  # a real email
# the password of the real email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'sitio@organilab.org')
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Celery settings
BROKER_URL = os.getenv(
    'BROKER_URL', 'amqp://guest:guest@localhost:5672/organilabvhost')
CELERY_TIMEZONE = TIME_ZONE
CELERY_MODULE = "organilab.celery"
CELERY_RESULT_BACKEND ="django-db"
CELERY_CACHE_BACKEND = 'django-cache'
#os.getenv('CELERY_RESULT_BACKEND', 'amqp://guest:guest@localhost:5672/organilabvhost')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',
    }
}
LOCATION_FIELD_PATH = STATIC_URL + 'location_field'
LOCATION_FIELD = {
    'map.provider': 'openstreetmap',
    'search.provider': 'nominatim',
    'map.zoom': 13,
    'search.suffix': '',
    'resources.root_path': LOCATION_FIELD_PATH,
}

ACCOUNT_ACTIVATION_DAYS = 2

ASYNC_NOTIFICATION_TEXT_AREA_WIDGET = 'markitup.widgets.AdminMarkItUpWidget'

from celery.schedules import crontab

CELERY_MODULE='organilab.celery'

CELERYBEAT_SCHEDULE = {
    # execute 12:30 pm
    'send_daily_emails': {
        'task': 'async_notifications.tasks.send_daily',
        'schedule': crontab(minute=2, hour=0),
    },
    'check_product_limits': {
        'task': 'laboratory.tasks.notify_about_product_limit_reach',
        'schedule': crontab(minute=50, hour=6),
    },
    'create_precursor_reports': {
        'task': 'laboratory.tasks.create_precursor_reports',
        'schedule': crontab(minute=2, hour=0, day_of_month=1),
    },
    'verify_precursor_reports': {
        'task': 'laboratory.tasks.verify_precursor_reports',
        'schedule': crontab(hour='*/6', day_of_month="*/2"),
    },
}

INTERNAL_IPS = ('127.0.0.1',)
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_CONFIGS = {
    'default': {
        'height': 500,
        'width': 'auto',
    },
}
ASYNC_SMTP_DEBUG=False
ASYNC_NEWSLETTER_WIDGET = 'markitup.widgets.AdminMarkItUpWidget'
MARKITUP_FILTER = ('markdown.markdown', {'safe_mode': True})
MARKITUP_SET = 'markitup/sets/markdown/'
JQUERY_URL = None

DATE_INPUT_FORMATS = [
    '%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y'
]

DATE_FORMAT = 'd/m/Y'

DATETIME_INPUT_FORMATS = [
    '%m/%d/%Y %H:%M %p',
    '%Y/%m/%d %H:%M %A',
    '%Y-%m-%d %H:%M %p',
    '%Y-%m-%d %H:%M',
    '%m/%d/%Y %H:%M',
    '%d/%m/%Y %H:%M',
    '%d/%m/%y %H:%M'
]

#Paypal configurations
PAYPAL_TEST = True
PAYPAL_RECEIVER_EMAIL = 'paypal@solvosoft.com'
MY_PAYPAL_HOST="http://localhost:8000/"

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY', 'MyRecaptchaKey123')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY', 'MyRecaptchaPrivateKey456')
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

GT_GROUP_MODEL='auth_and_perms.models.Rol'
DEFAULT_BUSSINESS = int(os.getenv('DEFAULT_BUSSINESS', 1))
DEFAULT_ENTITY = int(os.getenv('DEFAULT_ENTITY', 1))
DEFAULT_SUCCESS_BCCR=0

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

DJANGO_LOG_LEVEL=os.getenv('DJANGO_LOG_LEVEL', 'INFO')
DEFAULT_LOGGER_NAME='organilab'

LOGGING = {
   'version': 1,
   'disable_existing_loggers': False,
   'filters': {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
   'formatters': {
       "console": {
           "format": "{levelname} {asctime} {pathname} - line {lineno}: {message}",
           "style": "{",
       },
       'json': {
           'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
       },
   },
   'handlers': {
       'console': {
           'class': 'logging.StreamHandler',
           'stream': sys.stdout,
           'formatter': 'json'
       },

       "mail_admins": {
           "level": "ERROR",
           "filters": ["require_debug_false"],
           "class": "django.utils.log.AdminEmailHandler",
       }
   },
   'loggers': {
        DEFAULT_LOGGER_NAME: {
           'handlers': ['console'],
           'level': DJANGO_LOG_LEVEL,
           'propagate': True,
        },
        'django': {
           'handlers': ['console', "mail_admins"],
           'level': DJANGO_LOG_LEVEL,
           'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
        },
        'organilab_celery': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
        }
   },
}

if not DEBUG:
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DEFAULT_SHELF_ULIMIT=0
DEFAULT_MIN_QUANTITY = 0.0000001
