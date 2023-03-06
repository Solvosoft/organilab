from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from auth_and_perms.views.organizationstructure import getLevelClass, getTree
from laboratory.models import OrganizationStructure



@login_required
def select_organization_by_user(request, org_pk=None):
    query_list = OrganizationStructure.os_manager.filter_user_org(request.user)
    parents = list(query_list)
    nodes = []
    pks=[]
    for node in parents:
        if node.pk not in pks:
            getTrees(node, nodes, request.user, pks, level=0)

    context = {
        'nodes': nodes,
        'has_nodes': len(nodes)
    }

    return render(request, 'auth_and_perms/select_organization.html', context=context)

def getTrees(node, structure, user, pks, level=0):

    structure+=[(node,getLevelClass(level))]
    pks.append(node.pk)

    if node.children.exists():
        for child in node.descendants().filter(organizationusermanagement__users=user):
            if child.pk not in pks:
                getTrees(child, structure, user, pks, level=level+1)