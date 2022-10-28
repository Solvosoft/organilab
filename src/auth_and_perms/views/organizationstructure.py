from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from auth_and_perms.models import ProfilePermission, Rol, Profile
from laboratory.models import OrganizationStructure
from django.conf import settings


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
    context={'nodes': nodes }
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