from django.db.models import Q


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


def get_organization_tree(node, structure, user, pks, level=0, parents=[], append_info=True):
    structure += [(getNodeInformation(node) if append_info else node,  getLevelClass(level))]
    pks.append(node.pk)
    if node.children.all().exists():
        for child in node.descendants().filter(
                Q(users=user) | Q(pk__in=parents)).distinct():
            if child.pk not in pks:
                get_organization_tree(child, structure, user, pks, level=level + 1, parents=parents,
                                      append_info=append_info)
