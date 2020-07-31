from rest_framework.response import Response
from rest_framework.views import APIView

from laboratory.models import OrganizationStructure, OrganizationUserManagement


def get_users_button(pk_orga):
    users_button = "<a class='btn btn-primary btn-sm'" \
                   "onclick='users_management(this)'" \
                    " data-id='" + str(pk_orga) +"'><i class='fa fa-users'></i></a>"

    return users_button


def get_organization_button(pk_orga):
    organization_button = "<button type='button' class='btn btn-success btn-sm' onclick='update_pK_parent(this)'" \
                          " id='" + str(pk_orga) + "' data-toggle='modal'" \
                          " data-target='#organizationsavemodal'> <i class='fa fa-university'></i></button>"

    return organization_button


def get_child(element, query):
    list_child = []
    info_orga = {}

    for x in query.filter(organization__parent=element):
        pk = x.organization.pk
        buttons = "<div class='pull-right' style='margin-bottom:10px;'>" + get_organization_button(
            pk) + get_users_button(pk) + "</div>"

        info_orga = {
            'text': x.organization.name + buttons,
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
            pk = x.organization.pk
            buttons = "<div class='pull-right' style='margin-bottom:10px;'>" + get_organization_button(
                pk) + get_users_button(pk) + "</div>"
            text = text + buttons

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


def get_all_organizations(queryset):
    list_organization = []
    for x in queryset:
        list_organization.append(x.organization)
        if x.organization.parent:
            parent = queryset.filter(organization=x.organization.parent).first()
            if parent is None and parent not in list_organization:
                parent = OrganizationStructure.objects.get(pk=x.organization.parent.pk)
                list_organization.append(parent)

    return list_organization


class OrganizationStructureView(APIView):

    def get(self, request, format=None):
        tree = {}
        organizations_user = OrganizationUserManagement.objects.filter(users__in=[request.user])
        queryset = OrganizationUserManagement.objects.filter(
            organization__in=get_all_organizations(organizations_user)).order_by('organization__name')
        if queryset:
            tree = get_data_parent(queryset, request.user)

            new_orga = {
                'text': get_organization_button(0),
                'href': '#'
            }
            tree.append(new_orga)
            return Response(tree)
