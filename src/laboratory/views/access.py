# encoding: utf-8

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render
from laboratory.decorators import user_group_perms
from laboratory.forms import OrganizationUserManagementForm, SearchUserForm
from laboratory.models import OrganizationStructure, OrganizationUserManagement


@login_required
@user_group_perms(perm='laboratory.add_organizationstructure')
@user_group_perms(perm='laboratory.view_organizationstructure')
@user_group_perms(perm='laboratory.add_organizationusermanagement')
@user_group_perms(perm='laboratory.view_organizationusermanagement')
def access_management(request):
    context = {}
    parent = None

    if request.method == 'POST':
        user = request.user
        form = OrganizationUserManagementForm(request.POST)
        if form.is_valid():
            pk = int(request.POST["pk"])

            if pk > 0:
                parent = OrganizationStructure.objects.filter(pk=pk).first()

            orga = OrganizationStructure(name=form.cleaned_data['name'], parent=parent)
            orga.save()
            orga_user = OrganizationUserManagement(group=form.cleaned_data['group'], organization=orga)
            orga_user.save()
            orga_user.users.add(user)
            return redirect('laboratory:access_list')
    else:
        form = OrganizationUserManagementForm()

    context['form'] = form
    return render(request, 'laboratory/access_management.html', context=context)


@login_required
@user_group_perms(perm='laboratory.view_organizationstructure')
@user_group_perms(perm='laboratory.view_organizationusermanagement')
def users_management(request, pk):

    context = {}
    orga_user_managament = OrganizationUserManagement.objects.filter(organization__pk=pk).first()
    users_organization = orga_user_managament.users.all()
    users_pk = [user.pk for user in users_organization]

    if request.method == 'POST':
        form = SearchUserForm(request.POST, users_list=users_pk)
        if form.is_valid():
            user = form.cleaned_data['user']
            orga_user_managament.users.add(user)
            return redirect('laboratory:users_management', pk=pk)
    else:
        form = SearchUserForm(users_list=users_pk)

    context['form'] = form

    if orga_user_managament:
        context['users_list'] = users_organization
        context['organization'] = orga_user_managament.organization

    return render(request, 'laboratory/users_management.html', context=context)

@login_required
@user_group_perms(perm='laboratory.change_organizationusermanagement')
@user_group_perms(perm='laboratory.view_organizationusermanagement')
def delete_user(request, pk, user_pk):
    user_orga_management = OrganizationUserManagement.objects.filter(organization__pk=pk).first()
    if user_orga_management:
        user_orga_management.users.remove(user_pk)
    return redirect('laboratory:users_management', pk=pk)
