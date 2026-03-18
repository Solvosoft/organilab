from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from laboratory.models import (
    OrganizationStructure,
    Laboratory,
    Object,
    ShelfObjectEquipmentCharacteristics,
    ShelfObjectMaintenance,
    ShelfObjectLog,
    ShelfObjectCalibrate,
    ShelfObjectTraining,
    ShelfObjectGuarantee,
    Inform,
    InformScheduler,
    OrganizationStructureRelations,
    UserOrganization,
    ObjectLogChange,
    RegisterUserQR,
    InformsPeriod,
)


class Command(BaseCommand):
    help = "Mueve datos de una organización a otra."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-org",
            type=int,
            required=True,
            help="ID de la organización origen",
        )
        parser.add_argument(
            "--to-org",
            type=int,
            required=True,
            help="ID de la organización destino",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra qué se cambiaría, sin guardar cambios",
        )

    def handle(self, *args, **options):
        from_org_id = options["from_org"]
        to_org_id = options["to_org"]
        dry_run = options["dry_run"]

        if from_org_id == to_org_id:
            raise CommandError(
                "La organización origen y destino no pueden ser la misma."
            )

        try:
            from_org = OrganizationStructure.objects.get(pk=from_org_id)
        except OrganizationStructure.DoesNotExist:
            raise CommandError(f"No existe la organización origen con ID {from_org_id}")

        try:
            to_org = OrganizationStructure.objects.get(pk=to_org_id)
        except OrganizationStructure.DoesNotExist:
            raise CommandError(f"No existe la organización destino con ID {to_org_id}")

        counters = {
            "Laboratory.organization": Laboratory.objects.filter(
                organization=from_org
            ).count(),
            "Object.organization": Object.objects.filter(organization=from_org).count(),
            "ShelfObjectEquipmentCharacteristics.organization": ShelfObjectEquipmentCharacteristics.objects.filter(
                organization=from_org
            ).count(),
            "ShelfObjectMaintenance.organization": ShelfObjectMaintenance.objects.filter(
                organization=from_org
            ).count(),
            "ShelfObjectLog.organization": ShelfObjectLog.objects.filter(
                organization=from_org
            ).count(),
            "ShelfObjectCalibrate.organization": ShelfObjectCalibrate.objects.filter(
                organization=from_org
            ).count(),
            "ShelfObjectTraining.organization": ShelfObjectTraining.objects.filter(
                organization=from_org
            ).count(),
            "ShelfObjectGuarantee.organization": ShelfObjectGuarantee.objects.filter(
                organization=from_org
            ).count(),
            "Inform.organization": Inform.objects.filter(organization=from_org).count(),
            "InformScheduler.organization": InformScheduler.objects.filter(
                organization=from_org
            ).count(),
            "OrganizationStructureRelations.organization": OrganizationStructureRelations.objects.filter(
                organization=from_org
            ).count(),
            "UserOrganization.organization": UserOrganization.objects.filter(
                organization=from_org
            ).count(),
            "ObjectLogChange.organization_where_action_taken": ObjectLogChange.objects.filter(
                organization_where_action_taken=from_org
            ).count(),
            "RegisterUserQR.organization_creator": RegisterUserQR.objects.filter(
                organization_creator=from_org
            ).count(),
            "RegisterUserQR.organization_register": RegisterUserQR.objects.filter(
                organization_register=from_org
            ).count(),
            "InformsPeriod.organization": InformsPeriod.objects.filter(
                organization=from_org
            ).count(),
        }

        self.stdout.write(self.style.WARNING("Resumen de cambios:"))
        self.stdout.write(f"Origen:  {from_org.id} - {from_org.name}")
        self.stdout.write(f"Destino: {to_org.id} - {to_org.name}")
        self.stdout.write("")

        for label, count in counters.items():
            self.stdout.write(f"{label}: {count}")

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Dry-run: no se realizaron cambios."))
            return

        with transaction.atomic():
            Laboratory.objects.filter(organization=from_org).update(organization=to_org)
            Object.objects.filter(organization=from_org).update(organization=to_org)
            ShelfObjectEquipmentCharacteristics.objects.filter(
                organization=from_org
            ).update(organization=to_org)
            ShelfObjectMaintenance.objects.filter(organization=from_org).update(
                organization=to_org
            )
            ShelfObjectLog.objects.filter(organization=from_org).update(
                organization=to_org
            )
            ShelfObjectCalibrate.objects.filter(organization=from_org).update(
                organization=to_org
            )
            ShelfObjectTraining.objects.filter(organization=from_org).update(
                organization=to_org
            )
            ShelfObjectGuarantee.objects.filter(organization=from_org).update(
                organization=to_org
            )
            Inform.objects.filter(organization=from_org).update(organization=to_org)
            InformScheduler.objects.filter(organization=from_org).update(
                organization=to_org
            )
            OrganizationStructureRelations.objects.filter(organization=from_org).update(
                organization=to_org
            )
            UserOrganization.objects.filter(organization=from_org).update(
                organization=to_org
            )
            ObjectLogChange.objects.filter(
                organization_where_action_taken=from_org
            ).update(organization_where_action_taken=to_org)
            RegisterUserQR.objects.filter(organization_creator=from_org).update(
                organization_creator=to_org
            )
            RegisterUserQR.objects.filter(organization_register=from_org).update(
                organization_register=to_org
            )
            InformsPeriod.objects.filter(organization=from_org).update(
                organization=to_org
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Datos movidos correctamente."))
