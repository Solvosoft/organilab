from django.db.models import Q

from laboratory.models import OrganizationStructure


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
    cl = "col-md-12"
    if level:
        cl = "col-md-%d offset-md-%d" % (12 - level, level)
    return cl, color[level]


def getNodeInformation(node):
    users = []
    labs = node.laboratory_set.all()
    users += list(node.users.all())

    return {
        'node': node,
        'users': users,
        'labs': labs
    }

def get_descendants_by_org(pks, node, extras, user, parents):
    pks.append(node.pk)
    descendants = node.descendants().filter(**extras).filter(
        Q(users=user) | Q(pk__in=parents)).distinct().order_by('level', 'position')
    return descendants


def get_organization_tree(node, structure, user, pks, level=0, parents=[], append_info=True, extras={}):
    structure += [(getNodeInformation(node) if append_info else node,  getLevelClass(level))]
    descendants = get_descendants_by_org(pks, node, extras, user, parents)

    if descendants:
        for child in descendants:
            if child.pk not in pks:
                get_organization_tree(child, structure, user, pks, level=level + 1, parents=parents,
                                      append_info=append_info, extras=extras)

def get_tree_organization_pks_by_user(node, user, pks, parents=[], extras={}):
    descendants = get_descendants_by_org(pks, node, extras, user, parents)

    if descendants:
        for child in descendants:
            if child.pk not in pks:
                get_tree_organization_pks_by_user(child, user, pks, parents=parents,
                                      extras=extras)


def get_org_parents_info(user):
    query_list = OrganizationStructure.os_manager.filter_organization_by_user(
        user).distinct()
    parents = list(query_list.order_by('level'))
    parents_pks = set(query_list.values_list('pk', flat=True))
    return parents, parents_pks
