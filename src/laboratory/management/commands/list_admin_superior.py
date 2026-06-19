from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from laboratory.models import OrganizationStructure


class Command(BaseCommand):
    help = "List users with Administrativo superior role and export to .txt"

    def add_arguments(self, parser):
        parser.add_argument("--org-id", type=int, default=None, help="Filter by organization pk")
        parser.add_argument("--org-name", type=str, default=None, help="Filter by organization name (partial match)")
        parser.add_argument("--output", type=str, default="admin_superior_list.txt", help="Output file path")

    def handle(self, *args, **options):
        from auth_and_perms.models import ProfilePermission
        from collections import defaultdict

        org_ct = ContentType.objects.get_for_model(OrganizationStructure)
        pps = ProfilePermission.objects.filter(
            content_type=org_ct,
            rol__name="Administrativo superior",
        ).select_related("profile__user")

        if options["org_id"]:
            pps = pps.filter(object_id=options["org_id"])
        elif options["org_name"]:
            matching_orgs = OrganizationStructure.objects.filter(
                name__icontains=options["org_name"]
            ).values_list("pk", flat=True)
            pps = pps.filter(object_id__in=list(matching_orgs))

        by_org = defaultdict(list)
        for pp in pps:
            org = OrganizationStructure.objects.filter(pk=pp.object_id).first()
            if org is None:
                continue
            by_org[org].append(pp.profile.user)

        lines = []
        lines.append("=" * 80)
        lines.append("USUARIOS CON ROL: Administrativo superior")
        lines.append("=" * 80)

        if options["org_id"]:
            lines.append(f"Filtro: org pk={options['org_id']}")
        elif options["org_name"]:
            lines.append(f"Filtro: org nombre contiene '{options['org_name']}'")
        else:
            lines.append("Filtro: ninguno (todos)")

        total_unique = User.objects.filter(
            profile__profilepermission__content_type=org_ct,
            profile__profilepermission__object_id__in=[o.pk for o in by_org],
            profile__profilepermission__rol__name="Administrativo superior",
        ).distinct().count()

        lines.append(f"Total usuarios unicos: {total_unique}")
        lines.append(f"Total organizaciones: {len(by_org)}")
        lines.append("")

        for org, users in sorted(by_org.items(), key=lambda x: (x[0].level, x[0].name)):
            lines.append("-" * 80)
            lines.append(f"Organizacion : {org.name}")
            lines.append(f"pk={org.pk}  nivel={org.level}  padre={'ninguno' if not org.parent else org.parent.name}")
            lines.append(f"Usuarios     : {len(users)}")
            lines.append("")
            lines.append(f"  {'#':<4} {'Username':<40} {'Email':<40} {'Superuser'}")
            lines.append(f"  {'---':<4} {'-'*40} {'-'*40} {'-'*9}")
            for i, u in enumerate(sorted(users, key=lambda x: x.username), 1):
                sup = "Si" if u.is_superuser else "No"
                lines.append(f"  {str(i):<4} {u.username:<40} {u.email:<40} {sup}")
            lines.append("")

        lines.append("=" * 80)

        output_path = options["output"]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        self.stdout.write(self.style.SUCCESS(f"Archivo generado: {output_path}"))
        self.stdout.write(f"  {total_unique} usuarios en {len(by_org)} organizaciones")
