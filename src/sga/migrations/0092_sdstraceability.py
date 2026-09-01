import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import laboratory.models_utils


class Migration(migrations.Migration):
    """Trae SDSTraceability al estado de `sga` sin tocar la tabla.

    Complementa a laboratory.0215: allí se retira del estado de `laboratory` y
    aquí se declara en `sga`, apuntando a la misma tabla física.
    """

    dependencies = [
        ("laboratory", "0215_move_sdstraceability_to_sga"),
        ("sga", "0091_clean_abandoned_substance_drafts"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="SDSTraceability",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("creation_date", models.DateTimeField(auto_now_add=True)),
                        ("last_update", models.DateTimeField(auto_now=True)),
                        (
                            "source",
                            models.CharField(
                                choices=[
                                    ("merck", "Merck/Sigma-Aldrich"),
                                    ("pubchem", "PubChem"),
                                    ("fisher", "Fisher/Thermo"),
                                    ("panreac", "Panreac"),
                                    ("carlo_erba", "Carlo Erba"),
                                    ("jt_baker", "JT Baker"),
                                    ("honeywell", "Honeywell/Fluka"),
                                    ("unknown", "Unknown"),
                                    ("manual", "Manual upload"),
                                ],
                                default="unknown",
                                max_length=50,
                                verbose_name="SDS source",
                            ),
                        ),
                        (
                            "revision_date",
                            models.DateField(
                                blank=True, null=True, verbose_name="SDS revision date"
                            ),
                        ),
                        (
                            "download_url",
                            models.URLField(
                                blank=True,
                                default="",
                                max_length=500,
                                verbose_name="Download URL",
                            ),
                        ),
                        (
                            "security_sheet",
                            models.FileField(
                                blank=True,
                                null=True,
                                upload_to=laboratory.models_utils.upload_files,
                                verbose_name="Security sheet",
                            ),
                        ),
                        (
                            "verified_date",
                            models.DateField(
                                blank=True, null=True, verbose_name="Verified date"
                            ),
                        ),
                        (
                            "is_verified",
                            models.BooleanField(
                                default=False, verbose_name="Is verified"
                            ),
                        ),
                        (
                            "created_by",
                            models.ForeignKey(
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            "sga_substance_characteristics",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="sds_traceability",
                                to="sga.substancecharacteristics",
                            ),
                        ),
                        (
                            "verified_by",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="sds_verified_by",
                                to=settings.AUTH_USER_MODEL,
                                verbose_name="Verified by",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "SDS traceability",
                        "verbose_name_plural": "SDS traceability records",
                        "db_table": "laboratory_sdstraceability",
                        "ordering": ["-creation_date"],
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
