from rest_framework.response import Response
from rest_framework.views import APIView

from laboratory.models import OrganizationStructure, OrganizationUserManagement

organization_button = """
    <button type='button' class='btn btn-success btn-sm'>
    <i class='fa fa-university sm'></i></button>
    """
users_button = """
    <button type='button' class='btn btn-primary btn-sm'>
    <i class='fa fa-users'></i></button>
    """

buttons_action = "<div class='pull-right' style='margin-bottom:10px;'>" + organization_button + users_button + "</div>"

def get_child(element, query):

    list_child = []
    info_orga = {}

    for x in query.filter(organization__parent=element):

        buttons = "<div class='pull-right'>" +organization_button + users_button +"</div>"

        info_orga = {
            'text': x.organization.name + buttons_action,
            'href': '#' + str(x.organization.pk)
        }

        child = query.filter(organization__parent=x.organization)

        if child:
            info_orga['nodes'] = get_child(x.organization, query)

        list_child.append(info_orga)

    return list_child

def get_data_parent(queryset, user):

    orga_structure = []
    info_orga = {}
    queryset_orga_user = OrganizationUserManagement.objects.filter(users__in=[user])

    for x in queryset.filter(organization__parent=None):

        text = x.organization.name
        organization = queryset_orga_user.filter(organization=x.organization)

        if organization:
            text = text + buttons_action

        info_orga = {
            'text': text,
            'href': '#' + str(x.organization.pk)
        }

        list_child = queryset.filter(organization__parent=x.organization)

        if list_child:
            info_orga['nodes'] = get_child(x.organization, queryset)

        orga_structure.append(info_orga)
        info_orga = {}

    return orga_structure

def get_missing_parents(user, queryset):
    list_organization = []
    for x in queryset:
        if x.organization.parent:
            parent = queryset.filter(organization=x.organization.parent).first()
            if parent is None and parent not in list_organization:
                parent = OrganizationStructure.objects.get(pk=x.organization.parent.pk)
                list_organization.append(parent)
                list_organization.append(x.organization)

    list_organization = OrganizationUserManagement.objects.filter(organization__in=list_organization)

    return list_organization


class OrganizationStructureView(APIView):

    def get(self, request, format=None):
        queryset = OrganizationUserManagement.objects.filter(users__in=[request.user])
        list_with_parent = get_data_parent(queryset, request.user)
        list_without_parent = get_data_parent(get_missing_parents(request.user, queryset), request.user)
        tree = list_with_parent + list_without_parent
        return Response(tree)