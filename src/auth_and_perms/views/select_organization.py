from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from auth_and_perms.views.organizationstructure import getLevelClass
from laboratory.models import OrganizationStructure



@login_required
def select_organization_by_user(request):
    query_list = OrganizationStructure.os_manager.filter_user_org(request.user)
    parents = list(query_list)
    nodes = []
    position=0
    for parent in parents:
        position = 0
        for x in parent.descendants(include_self=True):

            level = (x, getLevelClass(position+1))
            if level not in nodes and x in parents:
                nodes+=[level]

    context = {
        'nodes': nodes,
        'has_nodes': len(nodes)
    }

    return render(request, 'auth_and_perms/select_organization.html', context=context)