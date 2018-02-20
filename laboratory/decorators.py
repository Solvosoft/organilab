from laboratory.models import Laboratory
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse
from laboratory.utils import check_lab_perms


def check_lab_permissions(function=None):

    def _decorate(view_function, *args, **kwargs):
        def view_wrapper(request, *args, **kwargs):
            lab_pk = kwargs.get('lab_pk')
            if lab_pk is not None:
                if not has_perm_in_lab(request.user, get_object_or_404(Laboratory, pk=lab_pk)):
                    return redirect(reverse('laboratory:permission_denied'))
            return view_function(request, *args, **kwargs)
        return view_wrapper

    if function:
        return _decorate(view_function=function)
    return _decorate

def has_perm_in_lab(user, lab):
    return user in lab.laboratorists.all() or user in lab.lab_admins.all()

def user_lab_perms(function=None, perm='search'):
    def _decorate(view_function, *args, **kwargs):
        def view_wrapper(request, *args, **kwargs):
            user = request.user
            lab = get_object_or_404(Laboratory, pk=request.session.get('lab_pk'))
            if not check_lab_perms(lab, user, perm):
                return redirect(reverse('laboratory:permission_denied'))
            return view_function(request, *args, **kwargs)
        return view_wrapper
    if function:
        return _decorate(view_function=function)
    return _decorate

def belongs_to_group(user, group):
    return bool(user.groups.filter(name=group))