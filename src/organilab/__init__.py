from __future__ import absolute_import

__version__ = '1.4.3'

if __name__ == '__main__':
    print(__version__)
else:
    from .celery import app as celery_app
