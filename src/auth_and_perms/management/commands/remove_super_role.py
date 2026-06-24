from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand, call_command
from django.db import connection
from django.conf import settings
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl import Workbook

from auth_and_perms.models import ProfilePermission, Profile
from laboratory.models import Laboratory, OrganizationStructure


class Command(BaseCommand):
    help = "Load permission category"

    def initial_data(self):
        self.pp = ProfilePermission.objects.filter(rol__name="Administrativo superior")
        self.profiles = Profile.objects.filter(
            pk__in=[p.profile.pk for p in self.pp]
        ).distinct()

    def handle(self, *args, **options):
        self.initial_data()
        wb = Workbook()
        ws = wb.active
        ws.title = "Roles grandes"

        headers = [
            "Nombre",
            "Correo",
            "Grupo",
            "Laboratorio",
            "Organización",
        ]
        header_font = Font(bold=True)
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal="center")

        row = 2
        data = []

        for profile in self.profiles:
            pp = self.pp.filter(
                profile=profile, rol__name="Administrativo superior"
            ).distinct()
            pro = profile.__str__()
            correo = profile.user.email
            grupo = profile.user.groups.filter(name="RegisterOrganization").exists()
            for p in pp:
                lab = ""
                org = ""
                pk = ""
                if p.content_type.app_label == "laboratory":
                    lab = (
                        Laboratory.objects.filter(pk=p.object_id).first().name
                        if Laboratory.objects.filter(pk=p.object_id).exists()
                        else "Desconocido"
                    )
                    pk = p.object_id

                    org = (
                        (
                            OrganizationStructure.objects.filter(pk=p.object_id)
                            .first()
                            .name
                        )
                        if OrganizationStructure.objects.filter(pk=p.object_id).exists()
                        else "Desconocido"
                    )
                elif p.content_type.app_label == "organization_structure":
                    org = (
                        OrganizationStructure.objects.filter(pk=p.object_id)
                        .first()
                        .name
                    )
                ws.cell(row=row, column=1, value=pro)
                ws.cell(row=row, column=2, value=correo)
                ws.cell(row=row, column=3, value=grupo)
                ws.cell(row=row, column=4, value=f"{lab}")
                ws.cell(row=row, column=5, value=org)
                pro = ""
                row += 1
                grupo = ""
                correo = ""
                for c in range(1, 5):
                    ws.cell(row=row, column=c).border = border
            pp.delete()
        for col in range(1, 5):
            ws.column_dimensions[get_column_letter(col)].width = 25

        wb.save("roles_grandes.xlsx")
