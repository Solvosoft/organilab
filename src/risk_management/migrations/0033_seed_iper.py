from django.db import migrations

from risk_management.iper_defaults import seed_iper


def load_iper(apps, schema_editor):
    Catalog = apps.get_model("laboratory", "Catalog")
    IPERRiskMatrix = apps.get_model("risk_management", "IPERRiskMatrix")
    IPERConfig = apps.get_model("risk_management", "IPERConfig")
    OrganizationStructure = apps.get_model("laboratory", "OrganizationStructure")
    seed_iper(Catalog, IPERRiskMatrix, IPERConfig, OrganizationStructure)


class Migration(migrations.Migration):

    dependencies = [
        ("risk_management", "0032_iperassessment_iperconfig_iperhazard_iperobservation_and_more"),
    ]

    operations = [
        migrations.RunPython(load_iper, reverse_code=migrations.RunPython.noop),
    ]
