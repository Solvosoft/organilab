import openpyxl
from django.conf import settings
from django.contrib.admin.models import ADDITION
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from auth_and_perms.models import Profile, ProfilePermission, Rol
from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    UserOrganization,
    OrganizationStructureRelations,
)
from laboratory.utils import organilab_logentry
from django.contrib.sites.models import Site


class Command(BaseCommand):

    help = "Actualiza características de sustancias desde un archivo Excel"

    def add_arguments(self, parser):
        site = Site.objects.get_current()
        url = f"https://{site.domain}"
        parser.add_argument(
            "doc",
            type=str,
            help="Ruta al archivo Excel (.xlsx) con los datos a procesar",
        )
        parser.add_argument(
            "--domain",
            type=str,
            default=url,
            help="Dominio para los enlaces en el correo (ej: https://organilab.org)",
        )

    def read_docs(self, documento, domain):
        self.rol = Rol.objects.get(name="Administrador de Laboratorio")
        try:
            wb = openpyxl.load_workbook(documento)
        except FileNotFoundError:
            raise CommandError(f"Archivo no encontrado: {documento}")
        except Exception as e:
            raise CommandError(f"Error al leer el archivo: {e}")
        ws = wb.active
        root = OrganizationStructure.objects.get(pk=1)
        groups = Group.objects.filter(name__in=["Profile", "PendingTasks"])
        for fila in ws.iter_rows(min_row=2, values_only=True):
            if not fila[3] or not fila[5] or not fila[1]:
                continue
            parent, parent_created = OrganizationStructure.objects.get_or_create(
                name=fila[3]
            )
            if parent_created:
                parent.parent = root
                parent.save()
            original_user, created_ori = User.objects.get_or_create(
                email=fila[0],
                defaults={"email": fila[0]},
            )
            self.create_profile(original_user)
            original_user.groups.add(*groups)
            original_user.save()
            if created_ori:
                password = get_random_string(12)
                original_user.first_name = fila[0] or ""
                original_user.username = fila[0]
                original_user.set_password(password)
                original_user.save()
                self.send_new_user_email(original_user, domain)
                organilab_logentry(
                    original_user,
                    original_user,
                    ADDITION,
                    "user",
                    changed_data=["username", "email", "first_name"],
                    change_message="User created via upload_org_and_users command",
                )

            org_child = None
            responsible2 = None
            responsible1, created = User.objects.get_or_create(
                email=fila[5],
                defaults={"email": fila[5], "first_name": fila[4] or ""},
            )
            responsible1.groups.add(*groups)
            responsible1.save()
            if created:
                password = get_random_string(12)
                responsible1.set_password(password)
                responsible1.username = fila[5]
                responsible1.save()
                self.send_new_user_email(responsible1, domain)
                organilab_logentry(
                    responsible1,
                    responsible1,
                    ADDITION,
                    "user",
                    changed_data=["username", "email", "first_name"],
                    change_message="User created via upload_org_and_users command",
                )
            self.create_profile(responsible1)

            if parent_created:
                organilab_logentry(
                    responsible1,
                    parent,
                    ADDITION,
                    "organizationstructure",
                    changed_data=["name"],
                    change_message="OrganizationStructure created via upload_org_and_users command",
                )

            content_type = ContentType.objects.get_for_model(OrganizationStructure)
            self.related_users_in_lab_org(original_user, content_type, root.pk, root)
            self.related_users_in_lab_org(
                original_user, content_type, parent.pk, parent
            )

            self.related_users_in_lab_org(responsible1, content_type, root.pk, root)
            self.related_users_in_lab_org(responsible1, content_type, parent.pk, parent)

            laboratory, lab_created = Laboratory.objects.get_or_create(name=fila[1])
            laboratory.responsible = responsible1
            laboratory.organization = root
            laboratory.save()
            if lab_created:
                organilab_logentry(
                    responsible1,
                    laboratory,
                    ADDITION,
                    "laboratory",
                    changed_data=["name", "responsible", "organization"],
                    change_message="Laboratory created via upload_org_and_users command",
                )
            lab_content_type = ContentType.objects.get_for_model(Laboratory)

            self.related_lab_in_org(responsible1, lab_content_type, laboratory.pk, root)
            self.related_lab_in_org(
                responsible1, lab_content_type, laboratory.pk, parent
            )
            self.related_lab_in_org(
                original_user, lab_content_type, laboratory.pk, root
            )
            self.related_lab_in_org(
                original_user, lab_content_type, laboratory.pk, parent
            )

            org_child = None
            if fila[2]:
                org_child = OrganizationStructure.objects.filter(name=fila[2]).first()
                if org_child:
                    org_child.parent = parent
                    org_child.save()
                else:
                    org_child, org_child_created = (
                        OrganizationStructure.objects.get_or_create(
                            name=fila[2], parent=parent
                        )
                    )
                    if org_child_created:
                        organilab_logentry(
                            responsible1,
                            org_child,
                            ADDITION,
                            "organizationstructure",
                            changed_data=["name", "parent"],
                            change_message="OrganizationStructure created via upload_org_and_users command",
                        )

            if fila[7]:
                responsible2, created = User.objects.get_or_create(
                    email=fila[7],
                    defaults={"email": fila[7], "first_name": fila[6] or ""},
                )
                responsible2.groups.add(*groups)
                responsible2.save()
                if created:
                    password = get_random_string(12)
                    responsible2.username = fila[7]
                    responsible2.set_password(password)
                    responsible2.save()
                    self.send_new_user_email(responsible2, domain)
                    organilab_logentry(
                        responsible2,
                        responsible2,
                        ADDITION,
                        "user",
                        changed_data=["username", "email", "first_name"],
                        change_message="User created via upload_org_and_users command",
                    )

                self.create_profile(responsible2)

                self.related_users_in_lab_org(responsible2, content_type, root.pk, root)
                self.related_users_in_lab_org(
                    responsible2, content_type, parent.pk, parent
                )
                self.related_lab_in_org(
                    responsible2, lab_content_type, laboratory.pk, root
                )
                self.related_lab_in_org(
                    responsible2, lab_content_type, laboratory.pk, parent
                )

                if org_child:
                    self.related_users_in_lab_org(
                        responsible1, content_type, org_child.pk, org_child
                    )
                    self.related_users_in_lab_org(
                        responsible2, content_type, org_child.pk, org_child
                    )
                    self.related_users_in_lab_org(
                        original_user, content_type, org_child.pk, org_child
                    )
                    self.related_lab_in_org(
                        responsible2, lab_content_type, laboratory.pk, org_child
                    )

            for org in [root, parent, org_child]:
                if org:
                    self.create_profile_permissions(
                        responsible1.profile,
                        lab_content_type,
                        laboratory.pk,
                        org,
                        self.rol,
                    )
                    if responsible2:
                        self.create_profile_permissions(
                            responsible2.profile,
                            lab_content_type,
                            laboratory.pk,
                            org,
                            self.rol,
                        )
                    if original_user:
                        self.create_profile_permissions(
                            original_user.profile,
                            lab_content_type,
                            laboratory.pk,
                            org,
                            self.rol,
                        )

    def send_new_user_email(self, user, domain):
        if not user.email:
            return
        context = {"user": user, "domain": domain}
        send_mail(
            subject="Nuevo usuario creado en la plataforma",
            message="Por favor use un visor de html",
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL,
            html_message=render_to_string(
                "gentelella/registration/new_user.html", context=context
            ),
        )
        self.stdout.write(self.style.SUCCESS(f"Correo enviado a {user.email}"))

    def create_profile(self, user):
        profile, created = Profile.objects.get_or_create(user=user)
        if created:
            organilab_logentry(
                user,
                profile,
                ADDITION,
                "profile",
                changed_data=["user"],
                change_message="Profile created via upload_org_and_users command",
            )
        return profile

    def create_profile_permissions(
        self, profile, content_type, object_id, organization, roles=None
    ):
        pp, _ = ProfilePermission.objects.get_or_create(
            profile=profile,
            content_type=content_type,
            object_id=object_id,
            organization=organization,
        )
        if profile.user.email in [
            "alonso.calvo.araya@una.cr",
            "allan.madrigal.mata@una.cr",
        ]:
            role = Rol.objects.get(name="Solo Lectura")
            pp.rol.add(role)
            pp.save()
        elif self.rol:
            pp.rol.add(self.rol)
            pp.save()

    def related_users_in_lab_org(self, users, content_type, object_id, organization):
        UserOrganization.objects.get_or_create(
            user=users,
            organization=organization,
            type_in_organization=UserOrganization.LABORATORY_MANAGER,
        )
        self.create_profile_permissions(
            users.profile,
            content_type,
            object_id,
            organization,
        )

    def related_lab_in_org(self, user, content_type, object_id, organization):
        relation, created = OrganizationStructureRelations.objects.get_or_create(
            organization=organization,
            content_type=content_type,
            object_id=object_id,
        )
        if created:
            organilab_logentry(
                user,
                relation,
                ADDITION,
                "organizationstructurerelations",
                changed_data=["organization", "content_type", "object_id"],
                change_message="OrganizationStructureRelations created via upload_org_and_users command",
            )

    def handle(self, *args, **options):
        self.rol = Rol.objects.get(name="Administrador de Laboratorio")
        self.read_docs(options["doc"], options["domain"])
