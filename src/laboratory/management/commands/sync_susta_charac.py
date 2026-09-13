import psycopg
from django.conf import settings
from django.core.management.base import BaseCommand

from laboratory.management.commands.sync_sds_from_old_db import (
    build_sga_map_by_object,
)
from sga.models import SubstanceCharacteristics

# Fichas de la base antigua que no deben copiarse: se revisaron a mano y su
# documento vigente es el que ya está en producción.
EXCLUDED_LEGACY_PKS = {
    944, 1521, 242, 923, 633, 586, 1622, 504, 408, 288, 968, 1630, 833, 795, 660,
}


class Command(BaseCommand):
    help = (
        "Copia las fichas de seguridad de laboratory_sustancecharacteristics de "
        "la base antigua a las características SGA equivalentes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que se copiaría sin escribir nada.",
        )
        parser.add_argument(
            "--db-name",
            default="oldOrganilab",
            help="Nombre de la base antigua (por defecto: oldOrganilab)",
        )

    def get_old_db_connection(self, db_name):
        db = settings.DATABASES["default"]
        return psycopg.connect(
            dbname=db_name,
            user=db["USER"],
            password=db["PASSWORD"],
            host=db["HOST"],
            port=db["PORT"],
            row_factory=psycopg.rows.dict_row,
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        db_name = options["db_name"]

        try:
            old_conn = self.get_old_db_connection(db_name)
        except Exception as e:
            self.stderr.write(f"No se puede conectar con {db_name}: {e}")
            return

        # Se lee por SQL en vez de por el modelo obsoleto: la base antigua
        # conserva su esquema propio y esto no depende de que
        # laboratory.SustanceCharacteristics siga declarado.
        with old_conn:
            with old_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, obj_id, security_sheet
                    FROM laboratory_sustancecharacteristics
                    WHERE cas_id_number IS NOT NULL
                      AND cas_id_number <> ''
                      AND security_sheet IS NOT NULL
                      AND security_sheet <> ''
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        old_conn.close()
        self.stdout.write(f"Encontradas {len(rows)} fichas en {db_name}")

        # La correspondencia va por el objeto de inventario compartido, igual que
        # en la migración laboratory.0211: los pks de ambas bases no coinciden.
        sga_by_object = build_sga_map_by_object()

        updated = 0
        skipped = 0
        for row in rows:
            if row["id"] in EXCLUDED_LEGACY_PKS:
                continue

            sga_pk = sga_by_object.get(row["obj_id"])
            if sga_pk is None:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] Copiaría {row['security_sheet']} a la "
                    f"característica SGA pk={sga_pk}"
                )
                updated += 1
                continue

            SubstanceCharacteristics.objects.filter(pk=sga_pk).update(
                security_sheet=row["security_sheet"]
            )
            updated += 1

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(f"\n{prefix}Resumen: copiadas={updated}, sin equivalente={skipped}")
