from django.contrib.auth.models import Permission
from django.core.management import BaseCommand

from auth_and_perms.models import Rol

ROLE_NAME = "Solo Lectura"

# Permissions the role must NOT have (write/delete capabilities it
# currently holds despite being a read-only role).
REMOVE_PERMISSIONS = [
    "laboratory.change_object",
    "laboratory.add_catalog",  # instrumental family is managed through Catalog
    "laboratory.change_catalog",  # instrumental family is managed through Catalog
    "laboratory.change_equipmenttype",
    "laboratory.change_objectfeatures",
    "laboratory.view_registeruserqr",
    "sga.add_dangerindication",
    "sga.add_warningword",
    "risk_management.add_incidentreport",
    "derb.add_customform",
    "academic.add_commentprocedurestep",
    "academic.change_commentprocedurestep",
    "academic.delete_commentprocedurestep",
    "academic.change_myprocedure",
    "blog.change_entry",
    "djreservation.add_reservation",
    "laboratory.add_registeruserqr",
    "laboratory.change_furniture",
    "laboratory.change_laboratory",
    "laboratory.change_laboratoryroom",
    "laboratory.change_shelf",
    "laboratory.change_shelfobjectlog",
    "reservations_management.add_reservations",
    "reservations_management.add_reservedproducts",
    "reservations_management.change_reservations",
    "risk_management.add_zonetype",
    "risk_management.change_incidentreport",
    "sga.add_substanceobservation",
    "sga.change_recipientsize",
    "laboratory.do_report",
    "laboratory.view_report",
    "laboratory.view_organizationstructure",
    "laboratory.view_organizationstructurerelations",
    "laboratory.add_registeruserqr",
    "auth_and_perms.view_profilepermission",
]

# View-only permissions the role is missing and should get.
ADD_PERMISSIONS = [
    "laboratory.view_laboratoryroom",
    "laboratory.view_shelf",
    "laboratory.view_furniture",
    "laboratory.view_provider",
    "academic.view_procedure",
    "laboratory.view_inform",
    "risk_management.view_buildings",
    "laboratory.view_sustancecharacteristics",  # reagent / substance characteristics
    "risk_management.view_structure",
    "laboratory.view_object",
    "laboratory.view_laboratoryprocess",
    "laboratory.view_shelfobjectobservation",
    "risk_management.view_riskzone",
    "risk_management.view_regent",
    "risk_management.view_workday",  # jornada laboral
    "reservations_management.view_reservations",  # jornada laboral
]


class Command(BaseCommand):
    help = (
        f"Clean up the '{ROLE_NAME}' role so it can't create, edit or delete "
        "anything: removes the write/delete permissions it shouldn't have and "
        "adds the view-only permissions it was missing."
    )

    def get_permission(self, app_codename):
        val = app_codename.split(".")
        if len(val) == 2:
            return Permission.objects.filter(
                codename=val[1], content_type__app_label=val[0]
            ).first()
        return None

    def resolve_permissions(self, codenames, label):
        perms = []
        for codename in codenames:
            perm = self.get_permission(codename)
            if perm:
                perms.append(perm)
            else:
                self.stdout.write(
                    self.style.WARNING(f"  [{label}] Permission not found: {codename}")
                )
        return perms

    def handle(self, *args, **options):
        rol = Rol.objects.filter(name=ROLE_NAME).first()
        if not rol:
            self.stdout.write(
                self.style.ERROR(f"Role '{ROLE_NAME}' does not exist. Aborting.")
            )
            return

        self.stdout.write(f"Cleaning role '{rol.name}' (id={rol.pk})...")

        self.stdout.write("\nResolving permissions to remove...")
        to_remove = self.resolve_permissions(REMOVE_PERMISSIONS, "REMOVE")
        if to_remove:
            rol.permissions.remove(*to_remove)
            for perm in to_remove:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [REMOVED] {perm.content_type.app_label}.{perm.codename}"
                    )
                )

        self.stdout.write("\nResolving permissions to add...")
        to_add = self.resolve_permissions(ADD_PERMISSIONS, "ADD")
        if to_add:
            rol.permissions.add(*to_add)
            for perm in to_add:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [ADDED] {perm.content_type.app_label}.{perm.codename}"
                    )
                )

        remaining_write_perms = rol.permissions.exclude(
            codename__startswith="view_"
        ).exclude(codename__startswith="can_view")
        if remaining_write_perms.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"\n[WARN] Role '{rol.name}' still has "
                    f"{remaining_write_perms.count()} non-view permission(s) left "
                    "(not covered by this cleanup, review manually):"
                )
            )
            for perm in remaining_write_perms.order_by(
                "content_type__app_label", "codename"
            ):
                self.stdout.write(f"    {perm.content_type.app_label}.{perm.codename}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Role '{rol.name}' now has {rol.permissions.count()} permission(s)."
            )
        )
