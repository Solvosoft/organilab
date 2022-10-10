from functools import wraps, WRAPPER_ASSIGNMENTS
from django.conf import settings
from sga.contextmanager import OrganilabContextManager


def organilab_context_decorator(function=None):
    def decorator(func):
        @wraps(func, assigned=WRAPPER_ASSIGNMENTS)
        def inner(request, *args, **kwargs):
            organilabcontext = kwargs.get('organilabcontext')
            if organilabcontext and organilabcontext in settings.ALLOWED_ORGANILAB_CONTEXT:
                with OrganilabContextManager(organilabcontext) as ocontext:
                    return func(request, *args, **kwargs)
            raise NotImplementedError('No organilabcontext in kwargs, see urls like path("<str:organilabcontext>", ...) ')
        return inner
    if function:
        return decorator(function)
    return decorator