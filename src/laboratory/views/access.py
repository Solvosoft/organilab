# encoding: utf-8
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User,Group
from django.shortcuts import redirect
from django.shortcuts import render
from laboratory.forms import OrganizationUserManagementForm, SearchUserForm
from laboratory.models import Laboratory, OrganizationStructure, OrganizationUserManagement, Profile
from laboratory.decorators import has_lab_assigned
from django.contrib import messages
from django.utils.translation import gettext as _
from laboratory.models import Profile,ProfilePermission


#FIXME to manage add separately bootstrap, we need a workaround to to this.
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
    return render(request, 'laboratory/access_management.html', context=context)

@has_lab_assigned(lab_pk='pk')
@permission_required('laboratory.view_organizationusermanagement')
def users_management(request, pk):
    if request.method == 'POST':
        users_list = Profile.objects.filter(laboratories__pk=pk).all()
        form = SearchUserForm(request.POST, users_list=users_list)
        if form.is_valid():
            user = User.objects.get(username=form.cleaned_data['user'])
            lab = Laboratory.objects.get(pk=pk)
            if not hasattr(user, 'profile'):
                profile = Profile(user=user)
                profile.save()
            user.profile.laboratories.add(lab)
            get_group = form.cleaned_data['group']
            group = Group.objects.get(pk=get_group.pk)
            group.user_set.add(user)
        return redirect('laboratory:users_management', pk=pk)
    users_pk = User.objects.filter(profile__laboratories__pk=pk).values_list('pk', flat=True)
    context = {
        'users_list': Profile.objects.filter(laboratories__pk=pk).all(),
        'organization': Laboratory.objects.get(pk=pk),
        'form': SearchUserForm(users_list=users_pk)
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
    return redirect('laboratory:users_management', pk=pk)
delete_user.lab_pk_field = 'pk'