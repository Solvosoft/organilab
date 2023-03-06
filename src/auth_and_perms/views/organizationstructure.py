from django import forms
from django.contrib.admin.models import ADDITION
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.conf import settings
from auth_and_perms.forms import AddUserForm, AddProfileRolForm, AddRolForm
from auth_and_perms.models import ProfilePermission, Rol, Profile
from auth_and_perms.utils import send_email
from authentication.forms import CreateUserForm
from laboratory.forms import AddOrganizationForm, RelOrganizationForm
from laboratory.models import OrganizationStructure, OrganizationUserManagement, Laboratory, \
    OrganizationStructureRelations, UserOrganization
from laboratory.utils import organilab_logentry
from laboratory.views.djgeneric import ListView, DeleteView


def getLevelClass(level):
    color = {
        0: 'default',
        1: 'danger',
        2: 'info',
        3: 'warning',
        4: 'default',
        5: 'danger',
        6: 'info'

    }
    level = level % 6
    cl="col-md-12"
    if level:
        cl="col-md-%d offset-md-%d"%(12-level, level)
    return cl, color[level]

def getNodeInformation(node):
    users=[]
    labs = node.laboratory_set.all()
    for orguser in node.organizationusermanagement_set.all():
        users += list(orguser.users.all())

    return {
        'node': node,
        'users': users,
        'labs': labs
    }

def getTree(node, structure, user, pks, level=0):

    klss=list(getLevelClass(level))
    pks.append(node.pk)
    klss.insert(0, getNodeInformation(node))
    structure.append(klss)

    if node.children.exists():
        for child in node.descendants().filter(organizationusermanagement__users=user):
            if child.pk not in pks:
                getTree(child, structure, user, pks, level=level+1)


@login_required
@permission_required("laboratory.change_organizationstructure")
def organization_manage_view(request):
    query_list = OrganizationStructure.os_manager.filter_user_org(request.user)
    parents=list(query_list)
    nodes = []
    pks=[]
    for node in parents:
        if node.pk not in pks:
            getTree(node, nodes,request.user,pks, level=0)

    context={'nodes': nodes,
             'adduserform': AddUserForm(),
             'addrolform': AddProfileRolForm(),
             'addorgform': AddOrganizationForm(),
             'relorgform': RelOrganizationForm()
             }
    return render(request, 'auth_and_perms/list_organizations.html', context)


def user_in_many_org(user):
    user_management = OrganizationUserManagement.objects.filter(users__in=[user])

    if user_management.exists():
        if user_management.count() > 1:
            return True
        else:
            return False


def delete_permissions(remove_perms_org, rol_list, user):
    keep_perms_orgs = set(rol_list.values_list('permissions', flat=True))
    remove_permissions = list(remove_perms_org.difference(keep_perms_orgs))
    user.user_permissions.remove(*remove_permissions)


def delete_rols(organizationstructure, keep_org_list, user, cc_lab):
    remove_rols = set(organizationstructure.rol.all().values_list('pk', flat=True))
    keep_rols_orgs = set(keep_org_list.values_list('pk', flat=True))
    remove_rols = list(remove_rols.difference(keep_rols_orgs))
    pp_list = ProfilePermission.objects.filter(content_type=cc_lab, profile__user=user, rol__pk__in=remove_rols)

    for pp in pp_list:
        pp.rol.remove(*remove_rols)


def delete_pp(cc_lab, user, org_labs):
    remove_pp = set(ProfilePermission.objects.filter(content_type=cc_lab, profile__user=user, object_id__in=org_labs).values_list('pk', flat=True))
    keep_pp_orgs = set(ProfilePermission.objects.filter(content_type=cc_lab, profile__user=user).exclude(
        object_id__in=org_labs).values_list('pk', flat=True))
    remove_pp = list(remove_pp.difference(keep_pp_orgs))
    ProfilePermission.objects.filter(pk__in=remove_pp).delete()

def get_related_users(user_management, form):
    set_old_users = set(user_management.users.all().values_list('pk', flat=True))
    set_new_users= set()
    if form.cleaned_data['users'] is not None:
        set_new_users = set(form.cleaned_data['users'].values_list('pk', flat=True))
    remove_users = set_old_users - set_new_users
    add_users = set_new_users - set_old_users
    return remove_users, add_users


@permission_required("laboratory.change_organizationusermanagement")
def add_users_organization(request, pk):

    organizationstructure = get_object_or_404(OrganizationStructure, pk=pk)
    user_management = organizationstructure.organizationusermanagement_set.first()
    permissions = list(organizationstructure.rol.filter(permissions__isnull=False).values_list('permissions', flat=True))

    if request.method == 'POST':

        form = AddUserForm(request.POST)
        if form.is_valid():

            remove_users, add_users = get_related_users(user_management, form)

            if remove_users:
                cc_lab = ContentType.objects.get(app_label='laboratory', model="laboratory")
                labs = organizationstructure.laboratory_set.all()
                org_labs = list(labs.values_list('pk', flat=True))


                for user in remove_users:
                    user = User.objects.get(pk=user)
                    pp_user = ProfilePermission.objects.filter(content_type=cc_lab, profile__user=user)
                    org_user = UserOrganization.objects.filter(user=user, organization=organizationstructure).first()
                    org_user.status = False
                    org_user.save()
                    if user_in_many_org(user): # check if user is in many organizations
                        org_filters = {
                            'users__in': [user],
                            'organization__rol__isnull': False,
                            'organization__rol__permissions__isnull': False
                        }
                        org_list = OrganizationUserManagement.objects.filter(**org_filters).exclude(organization__pk=organizationstructure.pk).distinct()
                        org_pk = list(org_list.values_list('organization__pk', flat=True))
                        pp_lab_list = list(OrganizationStructure.objects.filter(pk__in=org_pk).values_list('laboratory', flat=True).distinct())
                        rol_pk = list(pp_user.filter(object_id__in=pp_lab_list).values_list('rol__pk', flat=True).distinct())
                        rol_list = Rol.objects.filter(pk__in=rol_pk, permissions__isnull=False).distinct()

                        delete_permissions(set(permissions), rol_list, user)                    #step 1
                        delete_rols(organizationstructure, rol_list, user, cc_lab)             #step 2
                        delete_pp(cc_lab, user, org_labs)                                      #step 3

                    else:
                        user.user_permissions.remove(*permissions)
                        pp_user.filter(object_id__in=org_labs).delete()
                    user_management.users.remove(user)

            if add_users:
                user_management.users.add(*form.cleaned_data['users'])
                for user in add_users:
                    u, created = UserOrganization.objects.get_or_create(user=form.cleaned_data['users'].get(pk=user),
                                                           organization=organizationstructure)
                    if u:
                        u.status=True
                        u.save()

            messages.success(request, _("Element saved successfully"))
            return redirect('auth_and_perms:organizationManager')
    messages.error(request, _("Organization doesn't exists"))
    return redirect('auth_and_perms:organizationManager')


def assign_rol_permissions(user, rols):
    perms = list(rols.values_list('permissions', flat=True))
    user.user_permissions.add(*perms)


@method_decorator(permission_required("auth_and_perms.change_rol"), name="dispatch")
class ListRolByOrganization(ListView):
    model = Rol

    def get_queryset(self):
        queryset = super().get_queryset().filter(organizationstructure=self.org)
        return queryset


@method_decorator(permission_required("auth_and_perms.delete_rol"), name="dispatch")
class DeleteRolByOrganization(DeleteView):
    model = Rol

    def get_queryset(self):
        queryset = super().get_queryset().filter(organizationstructure=self.org)
        return queryset

    def get_success_url(self):
        return reverse('auth_and_perms:list_rol_by_org', args=[self.org])

def add_rol_by_laboratory(request):
    cc_lab = ContentType.objects.get(app_label='laboratory', model="laboratory")
    cc_org = ContentType.objects.get(app_label='laboratory', model="organizationstructure")

    if request.method == "POST":
        form = AddProfileRolForm(request.POST)

        if form.is_valid():
            org = OrganizationStructure.objects.get(pk=form.cleaned_data['org_pk'])
            lab = Laboratory.objects.get(pk=form.cleaned_data['lab_pk'])
            profile_list = ProfilePermission.objects.filter(content_type=cc_org, object_id =org.pk)

            for profile in profile_list:
                pp_lab = ProfilePermission.objects.filter(content_type=cc_lab, object_id =lab.pk, profile=profile.profile)

                if pp_lab.exists():
                    pp_lab = pp_lab.first()
                    pp_lab.rol.add(*form.cleaned_data['rols'])
                else:
                    pp_lab = ProfilePermission.objects.create(content_type=cc_lab, object_id=lab.pk, profile=profile.profile)
                    pp_lab.rol.add(*form.cleaned_data['rols'])
                assign_rol_permissions(pp_lab.profile.user, form.cleaned_data['rols'])

            messages.success(request, _("Element saved successfully"))
        else:
            messages.error(request, _("Error, form is invalid"))
    return redirect('auth_and_perms:organizationManager')




@method_decorator(permission_required("auth.add_user"), name="dispatch")
class AddUser(CreateView):
    model = User
    form_class = CreateUserForm

    def get(self, request, *args, **kwargs):
        self.organization = OrganizationUserManagement.objects.get(organization=kwargs.pop('pk'))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.organization = OrganizationUserManagement.objects.get(organization=kwargs.pop('pk'))
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, _("Element saved successfully"))
        return reverse('auth_and_perms:organizationManager')

    def form_valid(self, form):
        response = super().form_valid(form)
        password = User.objects.make_random_password()
        form.save()
        user = User.objects.filter(
            username=form.cleaned_data['username']
        ).first()
        user.password = password
        user.save()
        self.organization.users.add(user)
        UserOrganization.objects.create(organization=self.organization.organization, user=user)
        profile = Profile.objects.create(user=user, phone_number=form.cleaned_data['phone_number'],
                                         id_card=form.cleaned_data['id_card'],
                                         job_position=form.cleaned_data['job_position'])
        send_email(self.request, user)
        organilab_logentry(user, user, ADDITION, 'user', changed_data=['username', 'first_name', 'last_name', 'email', 'password'],
                           relobj=self.organization)
        organilab_logentry(user, profile, ADDITION, 'profile',
                           changed_data=['user', 'phone_number', 'id_card', 'job_position'],
                           relobj=self.organization)

        return response


@permission_required("laboratory.change_organizationusermanagement")
def add_contenttype_to_org(request):
    "contentyperelobj organization"
    contentyperelobj = request.POST.getlist('contentyperelobj', [])
    organization = get_object_or_404(OrganizationStructure, pk=request.POST.get('organization', '0'))
    if organization and contentyperelobj:
        for obj in contentyperelobj:
            OrganizationStructureRelations.objects.create(
                organization=organization,
                content_type=ContentType.objects.filter(
                    app_label='laboratory',
                    model='laboratory'
                ).first(),
                object_id=obj
            )
    return redirect('auth_and_perms:organizationManager')



@permission_required("laboratory.change_organizationstructure")
def copy_rols(request, pk):
    org = get_object_or_404(OrganizationStructure, pk=pk)

    if request.method == "POST":
        form = AddRolForm(request.POST)

        if form.is_valid():
            org.rol.add(*form.cleaned_data['rols'])
            messages.success(request, _("Element saved successfully"))
        else:
            messages.error(request, _("Error, form is invalid"))
    return redirect('auth_and_perms:organizationManager')