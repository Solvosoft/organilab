import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Q
from docutils.nodes import description

from laboratory.models import (
    Catalog,
    BaseUnitValues,
    Object,
    OrganizationStructure,
    SustanceCharacteristics,
    EquipmentType,
    MaterialCapacity,
    EquipmentCharacteristics,
)
from sga.models import DangerIndication


class Command(BaseCommand):

    help = "Migrate objects"

    # def add_arguments(self, parser):
    #     parser.add_argument("--from", type=str, default="default")
    #     parser.add_argument("--to", type=str, default="una")

    def handle(self, *args, **options):
        self.from_db = "default"
        self.to_db = "una"

        self.migrate_equipment_type()
        self.restore_objects()

    def migrate_equipment_type(self):
        equipment_type = EquipmentType.objects.using(self.from_db).all()
        for et in equipment_type:
            EquipmentType.objects.using(self.to_db).get_or_create(
                name=et.name,
                description=et.description,
            )

    def restore_objects(self):
        objects_produ = (
            Object.objects.using(self.from_db)
            .select_related("organization")
            .distinct("pk")
        )
        for obj in objects_produ:
            by_org = {
                "code": obj.code,
                "name": obj.name,
                "type": obj.type,
            }
            una_obj = Object.objects.using(self.to_db).filter(**by_org).distinct("pk")
            org_una = OrganizationStructure.objects.using(self.to_db).filter(
                name=obj.organization.name
            )
            if org_una.exists():
                if not una_obj.exists():
                    new_obj = Object.objects.using(self.to_db).create(
                        code=obj.code,
                        name=obj.name,
                        type=obj.type,
                        synonym=obj.synonym,
                        description=obj.description,
                        is_public=obj.is_public,
                        is_dangerous=obj.is_dangerous,
                        threshold=obj.threshold,
                        is_container=obj.is_container,
                        has_threshold=obj.has_threshold,
                        is_pure=obj.is_pure,
                        plaque=obj.plaque,
                        model=obj.model,
                        serie=obj.serie,
                        organization=org_una.first(),
                    )
                    features = list(
                        obj.features.using(self.to_db)
                        .filter(name__in=obj.features.values_list("name", flat=True))
                        .values_list("pk", flat=True)
                    )
                    new_obj.features.add(*features)
                    new_obj.save()
                    if obj.type == Object.REACTIVE and hasattr(
                        obj, "sustancecharacteristics"
                    ):
                        sus_char = obj.sustancecharacteristics
                        x = {
                            "obj": new_obj,
                            "cas_id_number": sus_char.cas_id_number,
                            "molecular_formula": sus_char.molecular_formula,
                            "is_precursor": sus_char.is_precursor,
                            "valid_molecular_formula": sus_char.valid_molecular_formula,
                            "seveso_list": sus_char.seveso_list,
                            "density": sus_char.density,
                            "security_sheet": (
                                sus_char.security_sheet
                                if sus_char.security_sheet
                                else None
                            ),
                            "img_representation": (
                                sus_char.img_representation
                                if sus_char.img_representation
                                else None
                            ),
                        }
                        z = (
                            ("iarc", "IARC"),
                            ("imdg", "IMDG"),
                            ("precursor_type", "Precursor"),
                        )
                        for field_name, value in z:
                            data = getattr(sus_char, field_name)

                            if data:
                                cat = Catalog.objects.using(self.to_db).filter(
                                    key=value,
                                    description=data.description,
                                )
                                if cat.exists():
                                    x.update(
                                        {
                                            field_name: cat.first(),
                                        }
                                    )
                        new_sus_char = SustanceCharacteristics.objects.using(
                            self.to_db
                        ).create(**x)
                        for field in [
                            "white_organ",
                            "ue_code",
                            "nfpa",
                            "storage_class",
                        ]:
                            if getattr(sus_char, field).exists():

                                for cat in (
                                    Catalog.objects.using(self.to_db)
                                    .filter(
                                        key=field,
                                        description__in=getattr(
                                            sus_char, field
                                        ).values_list("description", flat=True),
                                    )
                                    .all()
                                ):
                                    getattr(new_sus_char, field).add(cat)

                        for h in DangerIndication.objects.using(self.to_db).filter(
                            code__in=sus_char.h_code.values_list("code", flat=True)
                        ):
                            new_sus_char.h_code.add(h)
                        new_sus_char.save()
                    elif obj.type == Object.MATERIAL and hasattr(
                        obj, "materialcapacity"
                    ):
                        material_capacity_measurement_unit = (
                            Catalog.objects.using(self.to_db)
                            .filter(
                                key="units",
                                description=obj.materialcapacity.capacity_measurement_unit.description,
                            )
                            .first()
                        )
                        MaterialCapacity.objects.using(self.to_db).create(
                            object=new_obj,
                            capacity=obj.materialcapacity.capacity,
                            capacity_measurement_unit=material_capacity_measurement_unit,
                        )
                    elif obj.type == Object.EQUIPMENT and hasattr(
                        obj, "equipmentcharacteristics"
                    ):
                        equipment_type = (
                            EquipmentType.objects.using(self.to_db)
                            .filter(
                                name=obj.equipmentcharacteristics.equipment_type,
                                description=obj.equipmentcharacteristics.equipment_type,
                            )
                            .first()
                        )
                        EquipmentCharacteristics.objects.using(self.to_db).create(
                            object=new_obj,
                            equipment_type=equipment_type,
                            operation_voltage=obj.equipmentcharacteristics.operation_voltage,
                            operation_amperage=obj.equipmentcharacteristics.operation_amperage,
                            use_manual=obj.equipmentcharacteristics.use_manual,
                            use_specials_conditions=obj.equipmentcharacteristics.use_specials_conditions,
                            generate_pathological_waste=obj.equipmentcharacteristics.generate_pathological_waste,
                            clean_period_according_to_provider=obj.equipmentcharacteristics.clean_period_according_to_provider,
                        )
