import psycopg
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from laboratory.models import SDSTraceability, SustanceCharacteristics


class Command(BaseCommand):
    help = "Sync SDSTraceability records from oldOrganilab database into the current one"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_argument(
            "--db-name",
            default="oldOrganilab",
            help="Old database name (default: oldOrganilab)",
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

    def resolve_user_id(self, uid, existing_user_ids):
        if uid is None or uid not in existing_user_ids:
            return None
        return uid

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        db_name = options["db_name"]

        self.stdout.write(f"Connecting to old database: {db_name}")

        try:
            old_conn = self.get_old_db_connection(db_name)
        except Exception as e:
            self.stderr.write(f"Cannot connect to {db_name}: {e}")
            return

        with old_conn:
            with old_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        sustance_characteristics_id,
                        source,
                        revision_date,
                        download_url,
                        security_sheet,
                        verified_by_id,
                        verified_date,
                        is_verified,
                        created_by_id,
                        creation_date,
                        last_update
                    FROM laboratory_sdstraceability
                    ORDER BY id
                    """
                )
                rows = cur.fetchall()

        old_conn.close()

        self.stdout.write(f"Found {len(rows)} records in old database")

        existing_sc_ids = set(
            SustanceCharacteristics.objects.values_list("pk", flat=True)
        )
        existing_sds_ids = set(
            SDSTraceability.objects.values_list("pk", flat=True)
        )
        existing_user_ids = set(
            User.objects.values_list("pk", flat=True)
        )

        updated = 0
        created = 0
        skipped_no_sc = 0
        errors = 0

        for row in rows:
            pk = row["id"]
            sc_id = row["sustance_characteristics_id"]

            if sc_id not in existing_sc_ids:
                self.stderr.write(
                    f"[SKIP] id={pk}: SustanceCharacteristics pk={sc_id} not found"
                )
                skipped_no_sc += 1
                continue

            verified_by_id = self.resolve_user_id(row["verified_by_id"], existing_user_ids)
            created_by_id = self.resolve_user_id(row["created_by_id"], existing_user_ids)

            fields = {
                "sustance_characteristics_id": sc_id,
                "source": row["source"],
                "revision_date": row["revision_date"],
                "download_url": row["download_url"] or "",
                "security_sheet": row["security_sheet"] or "",
                "verified_by_id": verified_by_id,
                "verified_date": row["verified_date"],
                "is_verified": row["is_verified"],
                "created_by_id": created_by_id,
                "creation_date": row["creation_date"],
                "last_update": row["last_update"],
            }

            exists = pk in existing_sds_ids
            action = "update" if exists else "create"

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] Would {action} SDSTraceability id={pk} "
                    f"verified_by={verified_by_id} created_by={created_by_id}"
                )
                if exists:
                    updated += 1
                else:
                    created += 1
                continue

            try:
                if exists:
                    SDSTraceability.objects.filter(pk=pk).update(**fields)
                    self.stdout.write(f"[OK] Updated SDSTraceability id={pk}")
                    updated += 1
                else:
                    SDSTraceability.objects.create(id=pk, **fields)
                    existing_sds_ids.add(pk)
                    self.stdout.write(f"[CREATED] SDSTraceability id={pk}")
                    created += 1
            except Exception as e:
                self.stderr.write(f"[ERROR] id={pk} ({action}): {e}")
                errors += 1

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            f"\n{prefix}Summary: updated={updated}, created={created}, "
            f"skipped_no_sc={skipped_no_sc}, errors={errors}"
        )
