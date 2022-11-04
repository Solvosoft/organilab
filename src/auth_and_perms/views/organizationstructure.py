from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from django.conf import settings
from auth_and_perms.forms import AddUserForm, AddProfileRolForm
from auth_and_perms.models import ProfilePermission, Rol, Profile
from authentication.forms import CreateUserForm
from laboratory.models import OrganizationStructure, OrganizationUserManagement


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
        cl="col-md-offset-%d col-md-%d"%(level, 12-level)
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

def getTree(node, structure, level=0):
    klss=list(getLevelClass(level))
    klss.insert(0, getNodeInformation(node))
    structure.append(klss)
    if node.children.exists():
        for child in node.children.all():
            getTree(child, structure, level=level+1)


def organization_manage_view(request):
    query_list = OrganizationStructure.os_manager.filter_user(request.user)
    parents=list(query_list.filter(parent=None))
    nodes = []


    for node in parents:
        getTree(node, nodes, level=0)
    context={'nodes': nodes,
             'adduserform': AddUserForm(),
             'addrolform': AddProfileRolForm()
             }
    return render(request, 'auth_and_perms/list_organizations.html', context)

def manage_user_rolpermission(profilepermission, rol):
    old_user_permission = set(profilepermission.profile.user.user_permissions.all().values_list('pk', flat=True))
    set_permission_list = set(rol.permissions.all().values_list('pk', flat=True))
    add_permission = set_permission_list - old_user_permission
    remove_permission = old_user_permission - set_permission_list
    profilepermission.profile.user.user_permissions.add(*add_permission)
    profilepermission.profile.user.user_permissions.remove(*remove_permission)

@login_required
def update_user_rol(request, user_pk, rol_pk):
    response = {'result': 'error'}
    rol = get_object_or_404(Rol, pk=rol_pk)
    profilepermission = ProfilePermission.objects.filter(profile__user__pk=user_pk)

    if profilepermission.exists():
        profilepermission = profilepermission.first()
        if rol in profilepermission.rol.all():
            profilepermission.rol.remove(rol)
            response['removecheck'] = True
        else:
            profilepermission.rol.add(rol)
        manage_user_rolpermission(profilepermission, rol)
        response['result'] = 'ok'
    return JsonResponse(response)


def create_profile_permission(users, org_id, cc):
    for user in users:
        user = User.objects.get(pk=user)
        ProfilePermission.objects.create(profile=user.profile, content_type=cc, object_id=org_id)

def delete_profile_permission(users, org_id, cc):
    ProfilePermission.objects.filter(content_type=cc, object_id=org_id, profile__user__pk__in=users).delete()


def remove_user_permissions(user, rols):
    for rol in rols:
        permissions = rol.permissions.all()
        user.user_permissions.remove(*permissions)


def remove_org_rol(remove_users, oum):
    rols = []
    user_list = User.objects.filter(pk__in=list(remove_users))
    cc = ContentType.objects.get(app_label='laboratory', model="organizationstructure")
    for user in user_list:
        profile = Profile.objects.filter(user=user).first()

        pp = ProfilePermission.objects.filter(content_type=cc, profile=profile)
        oum_list = OrganizationUserManagement.objects.filter(users__in=[user])

        if oum_list.exists():
            if oum_list.all().count() == 1:
                rols = pp.rol.all()
                remove_user_permissions(user, rols)
                rols.delete()
            else:
                oum_rols = oum.rol.all()
                oum_list = oum_list.exclude(pk=oum.pk)

                for oum_obj in oum_list:
                    rols.append(oum_obj.rol.all())

                for rol in oum_rols:
                    if not rol in rols:
                        remove_user_permissions(user, [rol])
                        pp.rol.remove(rol)


@permission_required("laboratory.change_organizationusermanagement")
def add_users_organization(request, pk):

    organizationstructure = get_object_or_404(OrganizationStructure, pk=pk)
    cc = ContentType.objects.get(app_label='laboratory', model="organizationstructure")
    pp = ProfilePermission.objects.filter(content_type=cc)

    if request.method == 'POST':

        form = AddUserForm(request.POST)

        if form.is_valid():
            set_old_users = set(pp.filter(object_id=pk).values_list('profile__user__pk', flat=True))
            set_new_users = set(form.cleaned_data['users'].values_list('pk', flat=True))
            remove_users = set_old_users - set_new_users
            add_users = set_new_users - set_old_users

            if add_users:
                create_profile_permission(add_users, pk, cc)

            if remove_users:
                #delete profile permission in labs org by rol
                rols = organizationstructure.rol.all()
                labs = organizationstructure.laboratory_set.all()
                for user in remove_users:
                    org_profile = pp.filter(profile__user__pk=user)

                    if org_profile.all().count() > 1:
                        pass
                    else:
                        permissions = list(org_profile.values_list('rol__permissions', flat=True))

                        org_profile.delete()
                # Verifico si solo existe en una org si es asi entonces elimino todos los PP de ese perfil y permisos de los roles de esos PP
                # Si existe en más de una org checo primeramente si tienen laboratorios en común, sino entonces checo si se encuentra en otros lab con roles similares y descarto reviso permisos
                delete_profile_permission(remove_users, pk, cc)

            messages.success(request, _("Element saved successfully"))
            return redirect('auth_and_perms:organizationManager')
    messages.error(request, _("Organization doesn't exists"))
    return redirect('auth_and_perms:organizationManager')


def add_rol_by_laboratory(request):
    cc_lab = ContentType.objects.get(app_label='laboratory', model="laboratory")
    cc_org = ContentType.objects.get(app_label='laboratory', model="organizationstructure")

    if request.method == "POST":
        form = AddProfileRolForm(request.POST)

        if form.is_valid():
            org = OrganizationStructure.objects.get(form.cleaned_data['org_pk'])
            lab = OrganizationStructure.objects.get(form.cleaned_data['lab_pk'])
            profile_list = ProfilePermission.objects.filter(content_type=cc_org, object_id =org.pk)

            for profile in profile_list:
                pp_lab = ProfilePermission.objects.filter(content_type=cc_lab, object_id =lab.pk, profile=profile.profile)

                if pp_lab.exists():
                    pp_lab.first().rol.add(*form.cleaned_data['rols'])
                else:
                    pp_lab = ProfilePermission.objects.create(content_type=cc_lab, object_id=lab.pk, profile=profile.profile)
                    pp_lab.rol.add(*form.cleaned_data['rols'])

            messages.success(request, _("Element saved successfully"))
        messages.error(request, _("Error, form is invalid"))
    return redirect('organizationManager')


@method_decorator(permission_required("auth.add_user"), name="dispatch")
class AddUser(CreateView):
    model = User
    form_class = CreateUserForm

    def get_success_url(self):
        messages.success(self.request, _("Element saved successfully"))
        return reverse_lazy('auth_and_perms:organizationManager')

    def send_email(self, user):
        schema = self.request.scheme + "://"
        context = {
            'user': user,
            'domain': schema + self.request.get_host()
        }
        send_mail(subject="Nuevo usuario creado en la plataforma",
                  message="Por favor use un visor de html",
                  recipient_list=[user.email],
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  html_message=render_to_string(
                      'gentelella/registration/new_user.html',
                      context=context
                  )
                  )

    def form_valid(self, form):
        response = super().form_valid(form)
        password = User.objects.make_random_password()
        form.save()
        user = User.objects.filter(
            username=form.cleaned_data['username']
        ).first()
        user.password = password
        user.save()
        Profile.objects.create(user=user, phone_number=form.cleaned_data['phone_number'],
                                         id_card=form.cleaned_data['id_card'],
                                         job_position=form.cleaned_data['job_position'])
        self.send_email(user)
        group, created = Group.objects.get_or_create(name="General")
        group.user_set.add(user)
        return response