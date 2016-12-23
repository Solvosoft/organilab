from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import redirect
from django.urls import reverse

def verify_laboratory_session(func):
    def view_wrapper(*args, **kwargs):
        request = args[0]
        if isinstance(request, WSGIRequest) and request.user.is_authenticated:
                if request.session.get('lab_pk') is None:
                    return redirect(reverse('laboratory:select_lab'))
        return func(*args, **kwargs)
    return view_wrapper
