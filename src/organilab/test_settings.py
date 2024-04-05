from .settings import *

INSTALLED_APPS.append('organilab_test')

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

from logging import Filter

class NotInTestingFilter(Filter):

    def filter(self, record):
        from django.conf import settings

        return not settings.TESTING_MODE

TESTING_MODE=True
LANGUAGE_CODE='en'
DJANGO_LOG_LEVEL='DEBUG'

LOGGING = {
   'version': 1,
   'disable_existing_loggers': False,
   'formatters': {
       'verbose': {
           'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
       },
   },
   'handlers': {
       'console': {
           "class": "logging.FileHandler",
           "filename": "/organilab/logs/output.log",
       },
       "templates": {
           "level": "DEBUG",
           "class": "logging.FileHandler",
           "filename": "/organilab/logs/templates.log",
       },
   },
   'loggers': {
       'fontTools.subset': {
           'handlers': ['console'],
           'level': DJANGO_LOG_LEVEL,
           'propagate': True,
       },
       'root': {
           'handlers': ['console'],
           'level': DJANGO_LOG_LEVEL,
       },
       'django': {
           'handlers': ['console'],
           'level': "INFO",

       },
       'django.server': {
           'handlers': ['console'],
           'level': 'WARNING',

       },
        'django.template': {
            'handlers': ['templates'],
            'level': DJANGO_LOG_LEVEL,
        },
   },
}
