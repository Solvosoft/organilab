from laboratory.models import OrganizationStructure


def get_ancestor_org_pks(org_pk):
    """Return [org_pk] + PKs of all ancestors in the organization tree.

    Uses tree_queries .ancestors() which generates a single SQL query
    with a recursive CTE on PostgreSQL.
    """
    org = OrganizationStructure.objects.filter(pk=org_pk).first()
    if org is None:
        return [org_pk]
    return [org_pk] + list(
        org.ancestors().values_list("pk", flat=True)
    )


def get_descendant_org_pks(org_pk):
    """Return [org_pk] + PKs of all descendants in the organization tree.

    Uses tree_queries .descendants() which generates a single SQL query
    with a recursive CTE on PostgreSQL.
    """
    org = OrganizationStructure.objects.filter(pk=org_pk).first()
    if org is None:
        return [org_pk]
    return [org_pk] + list(
        org.descendants().values_list("pk", flat=True)
    )
