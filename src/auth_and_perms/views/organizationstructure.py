from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from auth_and_perms.forms import AddUserForm
from auth_and_perms.models import ProfilePermission, Rol
from laboratory.models import OrganizationStructure, OrganizationUserManagement
from django.utils.translation import gettext_lazy as _

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
    parents=list(OrganizationStructure.objects.filter(parent=None))
    nodes = []


    for node in parents:
        getTree(node, nodes, level=0)
    context={'nodes': nodes,
             'adduserform': AddUserForm()
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



def add_users_organization(request, pk):

    organizationstructure = get_object_or_404(OrganizationStructure, pk=pk)
    orgusersmanagement = OrganizationUserManagement.objects.filter(organization=organizationstructure)

    if request.method == 'POST':
        if orgusersmanagement.exists():
            form = AddUserForm(request.POST, instance=orgusersmanagement.first())
            if form.is_valid():
                form.save(commit=False)
                form.save_m2m()
                messages.success(request, _("Element saved successfully"))
                return redirect('auth_and_perms:organizationManager')
        messages.error(request, _("Organization doesn't exists"))
    return redirect('auth_and_perms:organizationManager')




