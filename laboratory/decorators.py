from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from laboratory.models import Laboratory

def verify_laboratory_session(func):
    def view_wrapper(*args, **kwargs):
        request = args[0]
        if isinstance(request, WSGIRequest) and request.user.is_authenticated:
                if request.session.get('lab_pk') is not None:
                    lab = get_object_or_404(Laboratory, pk=request.session.get('lab_pk'))
                    if not lab.laboratorists.filter(pk=request.user.pk).exists():
                        return redirect(reverse('laboratory:permission_denied'))
                else:
                    return redirect(reverse('laboratory:select_lab'))
        return func(*args, **kwargs)
    return view_wrapper
