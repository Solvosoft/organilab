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




LOGGING = {
   'version': 1,
   'disable_existing_loggers': True,
   'formatters': {
       'verbose': {
           'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
       },
   },
   'filters': {
            'testing': {
                '()': NotInTestingFilter
            }
        },

   'handlers': {
       'console': {
           'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
           'class': 'logging.StreamHandler',
           'stream': os.devnull,
           'formatter': 'verbose',
            'filters': ['testing']

       },
   },
   'loggers': {
       'fontTools.subset': {
           'handlers': ['console'],
           'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
           'propagate': True,
       },
       '': {
           'handlers': ['console'],
           'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
           'propagate': True,
       },
   },
}