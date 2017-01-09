from laboratory.models import Laboratory
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

def check_lab_permissions():
    def _decorate(view_function):
        def view_wrapper(request, *args, **kwargs):
            lab_pk = kwargs.get('lab_pk')
            if lab_pk is not None:
                if not has_perm_in_lab(request.user, Laboratory.objects.get(pk=lab_pk)):
                    return redirect(reverse('laboratory:permission_denied'))
            return view_function(request, *args, **kwargs)
        return view_wrapper
    return _decorate

def has_perm_in_lab(user, lab):
    return user in lab.laboratorists.all() or lab.lab_admins.all()