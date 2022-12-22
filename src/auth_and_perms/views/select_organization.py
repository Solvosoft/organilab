from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from auth_and_perms.views.organizationstructure import getLevelClass
from laboratory.models import OrganizationStructure



@login_required
def select_organization_by_user(request):
    query_list = OrganizationStructure.os_manager.filter_user(request.user)
    parents = list(query_list.filter(parent=None))
    nodes = []
    for parent in parents:
        nodes += [(x, getLevelClass(x.level)) for x in parent.descendants(include_self=True)]

    context = {
        'nodes': nodes,
        'has_nodes': len(nodes)
    }

    return render(request, 'auth_and_perms/select_organization.html', context=context)