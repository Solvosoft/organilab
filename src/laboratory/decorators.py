from django.db.models.query_utils import Q
from laboratory.models import Laboratory, OrganizationStructure
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from laboratory.utils import check_lab_group_has_perm, filter_laboratorist_profile_student


def check_perms(lab_pk, request, perm):
    user = request.user
    lab = None

    # User Admin can allway all
    if user.is_superuser:
        return True
    # redirect to select lab, if no login that send to login form
    if not lab_pk:
        redirect('laboratory:select_lab')
        return True
    else:
        lab = get_object_or_404(Laboratory, pk=lab_pk)

    # check if user have perms over lab
    lab_perms = check_lab_group_has_perm(
        user, lab, perm, filter_laboratorist_profile_student) if lab else False

    if not False in [lab_perms]:  # User have perms to all action level
        return True
    return False


""" Used to get perms with perm codename """


def user_group_perms(function=None, perm=None):
    def _decorate(view_function, *args, **kwargs):
        def view_wrapper(request, *args, **kwargs):
            lab_pk = kwargs.get('lab_pk')
            if not check_perms(lab_pk, request, perm):
                return redirect(reverse('permission_denied'))
            return view_function(request, *args, **kwargs)
        return view_wrapper
    if function:
        return _decorate(view_function=function)
    return _decorate


view_user_group_perms = user_group_perms
