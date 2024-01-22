from django.contrib import messages
from django.contrib.admin.models import ADDITION
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView
from auth_and_perms.forms import AddUserForm, AddProfileRolForm, AddRolForm, \
    ContentypeForm, OrganizationActions, ProfileGroupForm, IncludeEmailExternalUserForm, \
    OrganizationActionsClone, OrganizationActionsWithoutInactive
from auth_and_perms.forms import LaboratoryOfOrganizationForm, \
    ProfileListForm
from auth_and_perms.models import ProfilePermission, Rol, Profile
from auth_and_perms.node_tree import get_organization_tree, get_org_parents_info
from auth_and_perms.organization_utils import user_is_allowed_on_organization, organization_can_change_laboratory
from auth_and_perms.utils import send_email
from authentication.forms import CreateUserForm
from laboratory.forms import AddOrganizationForm, RelOrganizationForm
from laboratory.models import OrganizationStructure, Laboratory, \
    OrganizationStructureRelations, UserOrganization
from laboratory.utils import organilab_logentry, register_laboratory_contenttype
from laboratory.views.djgeneric import ListView, DeleteView
from django.conf import settings


@login_required
@permission_required("laboratory.change_organizationstructure")
def organization_manage_view(request):
    parents, parents_pks = get_org_parents_info(request.user)
    nodes = []
    pks=[]
    for node in parents:
        if node.pk not in pks:
            get_organization_tree(node, nodes,request.user,pks, level=0, parents=parents_pks, append_info=False)

    context={'nodes': nodes,
             'adduserform': AddUserForm(),
             'addrolform': AddProfileRolForm(),
             'addorgform': AddOrganizationForm(),
             'relorgform': RelOrganizationForm(),
             'labform': LaboratoryOfOrganizationForm(),
             'profileform': ProfileListForm(),
             'externaluserform': IncludeEmailExternalUserForm(),
             'actionform': OrganizationActions(),
             'actionwiform': OrganizationActionsWithoutInactive(prefix="wi"),
             'actioncloneform': OrganizationActionsClone(prefix="clone"),
             'profile_group_form': ProfileGroupForm(prefix="pg")
             }
    return render(request, 'auth_and_perms/list_organizations.html', context)


def user_in_many_org(user):
    user_management = UserOrganization.objects.filter(user=user).values_list('organization', flat=True).distinct()
    return len(set(user_management)) > 1


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

def get_related_users(organization, form):
    set_old_users = set(organization.users.all().values_list('pk', flat=True))
    set_new_users= set()
    if form.cleaned_data['users'] is not None:
        set_new_users = set(form.cleaned_data['users'].values_list('pk', flat=True))
    remove_users = set_old_users - set_new_users
    add_users = set_new_users - set_old_users
    return remove_users, add_users


@permission_required("laboratory.change_organizationstructure")
def add_users_organization(request, pk):

    organizationstructure = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=pk)
    user_is_allowed_on_organization(request.user, organizationstructure)
    permissions = list(organizationstructure.rol.using(settings.READONLY_DATABASE).filter(
        permissions__isnull=False).values_list('permissions', flat=True))

    if request.method == 'POST':

        form = AddUserForm(request.POST)
        if form.is_valid():
            remove_users, add_users = get_related_users(organizationstructure, form)
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
                            'rol__isnull': False,
                            'rol__permissions__isnull': False
                        }
                        org_list = OrganizationStructure.objects.filter(**org_filters).exclude(pk=organizationstructure.pk).distinct()
                        pp_lab_list = list(org_list.values_list('laboratory', flat=True).distinct())
                        rol_pk = list(pp_user.filter(object_id__in=pp_lab_list).values_list('rol__pk', flat=True).distinct())
                        rol_list = Rol.objects.filter(pk__in=rol_pk, permissions__isnull=False).distinct()

                        delete_permissions(set(permissions), rol_list, user)                    #step 1
                        delete_rols(organizationstructure, rol_list, user, cc_lab)             #step 2
                        delete_pp(cc_lab, user, org_labs)                                      #step 3

                    else:
                        user.user_permissions.remove(*permissions)
                        pp_user.filter(object_id__in=org_labs).delete()
                    organizationstructure.users.remove(user)

            if add_users:
                #user_management.users.add(*form.cleaned_data['users'])
                for user in add_users:
                    u, created = UserOrganization.objects.get_or_create(
                        user=form.cleaned_data['users'].get(pk=user),
                        status=True,
                        organization=organizationstructure, type_in_organization=UserOrganization.LABORATORY_USER)
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
        queryset = super().get_queryset().using(settings.READONLY_DATABASE).filter(organizationstructure=self.org)
        organization=get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=self.org)
        user_is_allowed_on_organization(self.request.user, organization)
        return queryset


@method_decorator(permission_required("auth_and_perms.delete_rol"), name="dispatch")
class DeleteRolByOrganization(DeleteView):
    model = Rol

    def get_queryset(self):
        queryset = super().get_queryset().using(settings.READONLY_DATABASE).filter(organizationstructure=self.org)
        organization=get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE), pk=self.org)
        user_is_allowed_on_organization(self.request.user, organization)
        return queryset

    def get_success_url(self):
        return reverse('auth_and_perms:list_rol_by_org', args=[self.org])

def add_rol_by_laboratory(request):
    cc_lab = ContentType.objects.get(app_label='laboratory', model="laboratory")
    cc_org = ContentType.objects.get(app_label='laboratory', model="organizationstructure")

    if request.method == "POST":
        form = AddProfileRolForm(request.POST)

        if form.is_valid():
            org = OrganizationStructure.objects.using(settings.READONLY_DATABASE).get(pk=form.cleaned_data['org_pk'])
            user_is_allowed_on_organization(request.user, org)
            lab = Laboratory.objects.get(pk=form.cleaned_data['lab_pk'])
            if not organization_can_change_laboratory(lab, org):
                return HttpResponseForbidden(_("Laboratory modification not authorized"))

            profile_list = ProfilePermission.objects.using(settings.READONLY_DATABASE).filter(
                content_type=cc_org, object_id =org.pk)

            for profile in profile_list:
                pp_lab = ProfilePermission.objects.filter(content_type=cc_lab, object_id=lab.pk,
                                                          profile=profile.profile)

                if pp_lab.exists():
                    pp_lab = pp_lab.first()
                    pp_lab.rol.add(*form.cleaned_data['rols'])
                else:
                    pp_lab = ProfilePermission.objects.create(content_type=cc_lab, object_id=lab.pk,
                                                              profile=profile.profile)
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
        self.organization = OrganizationStructure.objects.get(pk=kwargs.pop('pk'))
        user_is_allowed_on_organization(request.user, self.organization)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.organization = OrganizationStructure.objects.get(pk=kwargs.pop('pk'))
        user_is_allowed_on_organization(request.user, self.organization)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, _("Element saved successfully"))
        return reverse('auth_and_perms:organizationManager')

    def form_valid(self, form):
        response =  HttpResponseRedirect(self.get_success_url())
        password = User.objects.make_random_password()
        user = form.save(commit=True)
        user.username=form.cleaned_data['email']
        user.password = password
        user.save()
        #self.organization.users.add(user)
        UserOrganization.objects.create(organization=self.organization, user=user)
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


@permission_required("laboratory.change_organizationstructure")
def add_contenttype_to_org(request):
    form = ContentypeForm(request.POST)
    if form.is_valid():
        organization = get_object_or_404(OrganizationStructure.objects.using(settings.READONLY_DATABASE),
                                         pk=form.cleaned_data['organization'])
        user_is_allowed_on_organization(request.user, organization)
        contentyperelobj = form.cleaned_data['contentyperelobj'].values_list('pk',flat=True)
        for obj in contentyperelobj:
            register_laboratory_contenttype(organization, obj)
    else:
        raise Http404(_("Form data is wrong, you need to pass a valid laboratory as contenttype"))
    return redirect('auth_and_perms:organizationManager')



@permission_required("laboratory.change_organizationstructure")
@require_http_methods(["POST"])
def copy_rols(request, pk):
    org = get_object_or_404(OrganizationStructure, pk=pk)
    form = AddRolForm(request.POST)
    if form.is_valid():
        org.rol.add(*form.cleaned_data['rols'])
        messages.success(request, _("Element saved successfully"))
    else:
        messages.error(request, _("Error, form is invalid"))
    return redirect('auth_and_perms:organizationManager')
