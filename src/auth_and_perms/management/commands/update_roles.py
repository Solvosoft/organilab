import logging

from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand
from django.db import transaction

from auth_and_perms.management.roles import ROLE_DEFINITIONS, ROOT_ORGANIZATION
from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure

logger = logging.getLogger(__name__)

# Se crea uno por organización raíz al registrarla (views/user_org_creation.py).
PER_ORGANIZATION = {"organization_management"}

REGISTER_ORGANIZATION_GROUP = [
    "ambiental.view_measurementpoint",
    "ambiental.view_consumptionrecord",
    "ambiental.view_normalizationbase",
    "ambiental.view_ambiental_dashboard",
    "ambiental.view_consumptionalert",
    "ambiental.add_consumptionrecord",
    "ambiental.change_consumptionrecord",
    "ambiental.delete_consumptionrecord",
    "ambiental.add_measurementpoint",
    "ambiental.change_measurementpoint",
    "ambiental.delete_measurementpoint",
    "ambiental.add_normalizationbase",
    "ambiental.change_normalizationbase",
    "ambiental.delete_normalizationbase",
    "ambiental.preload_normalizationbase",
    "ambiental.review_consumptionalert",
    "ambiental.manage_building_access",
    "laboratory.view_report",
    "laboratory.do_report",
    "presentation.view_systemparameter",
    "presentation.change_systemparameter",
    "presentation.view_notificationsetting",
    "presentation.change_notificationsetting",
    "presentation.view_alertrule",
    "presentation.add_alertrule",
    "presentation.change_alertrule",
    "presentation.delete_alertrule",
    "djgentelella.view_trash",
    "djgentelella.change_trash",
    "djgentelella.delete_trash",
]


def permission_map():
    return {
        "%s.%s" % (perm.content_type.app_label, perm.codename): perm
        for perm in Permission.objects.select_related("content_type")
    }


def resolve_permissions(perms, available, warn):
    found = []
    for perm_str in perms:
        perm = available.get(perm_str)
        if perm is None:
            warn("permiso '%s' no existe, se omite" % perm_str)
        else:
            found.append(perm)
    return found


def sync_role(key, definition, available, warn):
    description = definition["description"]
    wanted = resolve_permissions(definition["permissions"], available, warn)
    wanted_ids = {perm.pk for perm in wanted}

    roles = list(Rol.objects.filter(name=definition["name"]))
    created = False
    if not roles:
        if key in PER_ORGANIZATION:
            return []
        roles = [Rol.objects.create(name=definition["name"], description=description)]
        created = True
        root = OrganizationStructure.objects.filter(name=ROOT_ORGANIZATION, parent__isnull=True).first()
        if root:
            root.rol.add(roles[0])
        else:
            warn("organización '%s' no existe, '%s' queda sin asociar" % (ROOT_ORGANIZATION, definition["name"]))

    changes = []
    for rol in roles:
        current_ids = set(rol.permissions.values_list("pk", flat=True))
        added = wanted_ids - current_ids
        removed = current_ids - wanted_ids
        rol.permissions.add(*added)
        rol.permissions.remove(*removed)
        description_changed = (rol.description or "") != description
        if description_changed:
            rol.description = description
            rol.save(update_fields=["description"])
        changes.append({
            "rol": rol,
            "created": created,
            "added": sorted(p.codename for p in Permission.objects.filter(pk__in=added)),
            "removed": sorted(p.codename for p in Permission.objects.filter(pk__in=removed)),
            "description": description_changed,
        })
    return changes


def sync_roles(keys=None, warn=logger.warning):
    available = permission_map()
    changes = []
    for key in keys or ROLE_DEFINITIONS:
        changes += sync_role(key, ROLE_DEFINITIONS[key], available, warn)
    return changes


def update_group_permissions(warn=logger.warning):
    group = Group.objects.filter(name="RegisterOrganization").first()
    if group:
        group.permissions.add(*resolve_permissions(REGISTER_ORGANIZATION_GROUP, permission_map(), warn))


class Command(BaseCommand):
    help = "Deja los roles igual que auth_and_perms/management/roles.py. Se puede correr varias veces."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                            help="Muestra los cambios sin guardarlos.")

    def warn(self, message):
        self.stdout.write(self.style.WARNING("WARNING: %s" % message))

    def handle(self, *args, **options):
        with transaction.atomic():
            changes = sync_roles(warn=self.warn)
            update_group_permissions(warn=self.warn)
            if options["dry_run"]:
                transaction.set_rollback(True)

        for change in changes:
            if not (change["created"] or change["added"] or change["removed"] or change["description"]):
                continue
            rol = change["rol"]
            self.stdout.write("%s%s (pk=%s): +%d -%d%s" % (
                rol.name,
                " [nuevo]" if change["created"] else "",
                rol.pk if not options["dry_run"] or not change["created"] else "-",
                len(change["added"]),
                len(change["removed"]),
                ", descripción" if change["description"] else "",
            ))
            if change["removed"]:
                self.stdout.write("    quita: %s" % ", ".join(change["removed"]))
        self.stdout.write("Sin guardar (--dry-run)." if options["dry_run"] else "Roles actualizados.")
