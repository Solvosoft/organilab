# encoding: utf-8

from constance import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from laboratory.decorators import user_group_perms
from laboratory.forms import UserCreate, UserSearchForm, OrganizationUserManagementForm, SearchUserForm
from laboratory.models import Laboratory, OrganizationStructure, OrganizationUserManagement
from laboratory.views.djgeneric import ListView


@method_decorator(login_required, name='dispatch')
class BaseAccessListLab(FormView, ListView):
    model = User
    template_name = 'laboratory/users_management.html'
    form_class = UserSearchForm
    user_create_form = UserCreate
    paginate_by = 30
    role = 0
    group = None
    search_user = None

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return super(BaseAccessListLab, self).post(request, *args, **kwargs)

    def get_queryset(self):
        if not self.search_user:
            return self.get_relationfield().all().order_by('pk')
        return self.get_relationfield().filter(pk__in=self.search_user).order_by('pk')

    def get_context_data(self, **kwargs):
        context = super(BaseAccessListLab, self).get_context_data(
            **kwargs)
        context.update(FormView.get_context_data(self, **kwargs))
        context['role'] = self.role
        context['user_create_form'] = self.user_create_form()
        return context

    def add_user_to_relation(self, user, relation, group_name):
        group = Group.objects.get(pk=group_name)
        user.groups.add(group)
        if not relation.filter(id=user.pk).exists():
            relation.add(user)

    def remove_user_to_relation(self, user, relation, group_name):
        pass

    def form_valid(self, form):
        if form.cleaned_data['action'] == 'add':
            users = User.objects.filter(pk__in=form.cleaned_data['user'])
            relation_field = self.get_relationfield()
            for user in users:
                self.add_user_to_relation(user, relation_field,
                                          self.group)
            messages.info(self.request, "User added successfully")
            return redirect(self.get_success_url())

        elif form.cleaned_data['action'] == 'createuser':
            user_create_form = UserCreate(self.request.POST)
            if user_create_form.is_valid():
                user = user_create_form.save()
                self.add_user_to_relation(user, self.get_relationfield(),
                                          self.group)
                messages.info(self.request, _("User added successfully"))
                return redirect(self.get_success_url())
            else:
                self.object_list = self.get_queryset()
                context = self.get_context_data()
                context['user_create_form'] = user_create_form
                              
                return render(self.request, self.template_name,
                              context)
                              
        elif form.cleaned_data['action'] == 'rmuser':
            users = User.objects.filter(
                pk__in=self.request.POST.getlist('user'))
            relation_field = self.get_relationfield()
            for user in users:
                self.remove_user_to_relation(user, relation_field, self.group)
            messages.info(self.request, _("Users removed successfully"))
            return redirect(self.get_success_url())
        else:
            self.search_user = form.cleaned_data['user']
            kwargs = {'lab_pk': self.lab}
            return self.get(self.request, **kwargs)

    def get_success_url(self):
        return reverse(self.success_url,
                       kwargs={'lab_pk': self.lab})

    def get_relationfield(self):
        pass

class AccessListLabAdminsView(BaseAccessListLab):
    role = '#tab_lab_admins'
    group = config.GROUP_ADMIN_PK
    success_url = 'laboratory:access_list_lab_admins'

    def get_relationfield(self):
        laboratory = get_object_or_404(Laboratory, pk=self.lab)
        return laboratory.lab_admins

    def remove_user_to_relation(self, user, relation, group_pk):
        group = Group.objects.get(pk=group_pk)
        relation.remove(user)
        if not user.lab_admins.all().exists():
            user.groups.remove(group)

@login_required
@permission_required('laboratory.add_organizationstructure')
@permission_required('laboratory.view_organizationstructure')
@permission_required('laboratory.add_organizationusermanagement')
@permission_required('laboratory.view_organizationusermanagement')
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
@permission_required('laboratory.view_organizationstructure')
@permission_required('laboratory.view_organizationusermanagement')
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
@permission_required('laboratory.change_organizationusermanagement')
@permission_required('laboratory.view_organizationusermanagement')
def delete_user(request, pk, user_pk):
    user_orga_management = OrganizationUserManagement.objects.filter(organization__pk=pk).first()
    if user_orga_management:
        user_orga_management.users.remove(user_pk)
    return redirect('laboratory:users_management', pk=pk)
