# encoding: utf-8
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect
from django.shortcuts import render
from laboratory.forms import OrganizationUserManagementForm, SearchUserForm, ProfilePermissionForm
from laboratory.models import Laboratory, OrganizationStructure, OrganizationUserManagement, Profile
from laboratory.decorators import has_lab_assigned
from django.contrib import messages
from django.utils.translation import gettext as _
from laboratory.models import Profile, ProfilePermission
from django.http import JsonResponse


# FIXME to manage add separately bootstrap, we need a workaround to to this.
@permission_required(['laboratory.view_organizationusermanagement', 'laboratory.add_organizationusermanagement'])
def access_management(request):
    context = {}
    parent = None
    if request.method == 'POST':
        form = OrganizationUserManagementForm(request.POST)
        if form.is_valid():
            pk = int(request.POST["pk"])

            if pk > 0:
                parent = OrganizationStructure.objects.filter(pk=pk).first()

            orga = OrganizationStructure(name=form.cleaned_data['name'], parent=parent)
            orga.save()
            orga_user = OrganizationUserManagement(group=form.cleaned_data['group'], organization=orga)
            orga_user.save()
            orga_user.users.add(request.user)
            messages.success(request, _('Organization added sucessfully'))
            return redirect('laboratory:access_list')
    else:
        form = OrganizationUserManagementForm()
    context['labs'] = request.user.profile.laboratories.all()
    context['orgs'] = OrganizationStructure.objects.filter(organizationusermanagement__users=request.user)
    context['form'] = form
    context['groups'] = Group.objects.all()
    return render(request, 'laboratory/access_management.html', context=context)


@has_lab_assigned(lab_pk='pk')
@permission_required('laboratory.view_organizationusermanagement')
def users_management(request, pk):
    if request.method == 'POST':
        users_list = Profile.objects.filter(laboratories__pk=pk).all()
        form = ProfilePermissionForm(request.POST, users_list=users_list)
        if form.is_valid():
            user = User.objects.get(username=form.cleaned_data['user'])
            lab = Laboratory.objects.get(pk=pk)
            roles = form.cleaned_data['rol']
            if not hasattr(user, 'profile'):
                profile = Profile(user=user)
                profile.save()
            user.profile.laboratories.add(lab)
            profile_permission = ProfilePermission.objects.create(profile=user.profile, laboratories=lab)
            if roles is not None:
                for rol in roles:
                    profile_permission.rol.add(rol)

            group, created = Group.objects.get_or_create(name="General")
            group.user_set.add(user)

        return redirect('laboratory:users_management', pk=pk)
    users_pk = User.objects.filter(profile__laboratories__pk=pk).values_list('pk', flat=True)
    context = {
        'users_list': Profile.objects.filter(laboratories__pk=pk).all(),
        'organization': Laboratory.objects.get(pk=pk),
        'form': ProfilePermissionForm(users_list=users_pk)
    }
    return render(request, 'laboratory/users_management.html', context=context)


users_management.lab_pk_field = 'pk'


@has_lab_assigned(lab_pk='pk')
@permission_required('laboratory.delete_organizationusermanagement')
def delete_user(request, pk, user_pk):
    lab = Laboratory.objects.filter(pk=pk).first()
    user = Profile.objects.filter(pk=user_pk).first()
    if user and lab:
        user.laboratories.remove(pk)
        pp = ProfilePermission.objects.filter(profile=user, laboratories=lab).first()
        if pp is not None:
            pp.delete()
    return redirect('laboratory:users_management', pk=pk)


delete_user.lab_pk_field = 'pk'

@permission_required('laboratory.change_organizationusermanagement')
def edit_management(request):
    parent = None
    if request.method == 'POST':
        pk = int(request.POST["org_pk"])
        orga=OrganizationStructure.objects.filter(pk=pk).first()
        orga.name = request.POST["name"]
        orga.save()
        messages.success(request, _('Organization added sucessfully'))
        return redirect('laboratory:access_list')

