import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models


class Command(BaseCommand):
    help = "Encuentra y elimina archivos en MEDIA_ROOT que no están referenciados en la base de datos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra los archivos huérfanos sin eliminarlos",
        )
        parser.add_argument(
            "--exclude-dirs",
            nargs="*",
            default=["editorupload"],
            help="Directorios dentro de MEDIA_ROOT a excluir (default: editorupload)",
        )

    def _get_referenced_files(self):
        """Recopila todos los paths de archivos referenciados en FileField/ImageField."""
        referenced = set()
        for model in apps.get_models():
            file_fields = [
                f.name for f in model._meta.get_fields()
                if isinstance(f, (models.FileField, models.ImageField))
            ]
            if not file_fields:
                continue

            for field_name in file_fields:
                values = (
                    model.objects.exclude(**{field_name: ""})
                    .exclude(**{field_name: None})
                    .values_list(field_name, flat=True)
                )
                for val in values.iterator():
                    if val:
                        referenced.add(val)
        return referenced

    def _get_media_files(self, exclude_dirs):
        """Recorre MEDIA_ROOT y retorna todos los archivos con su path relativo."""
        media_root = settings.MEDIA_ROOT
        media_files = set()
        for root, dirs, files in os.walk(media_root):
            # Excluir directorios
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for filename in files:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, media_root)
                media_files.add(rel_path)
        return media_files

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        exclude_dirs = options["exclude_dirs"] or []
        media_root = settings.MEDIA_ROOT

        if not os.path.isdir(media_root):
            self.stderr.write(f"MEDIA_ROOT no existe: {media_root}")
            return

        self.stdout.write(f"MEDIA_ROOT: {media_root}")
        self.stdout.write(f"Directorios excluidos: {exclude_dirs}")
        self.stdout.write("Recopilando archivos referenciados en la BD...")

        referenced_files = self._get_referenced_files()
        self.stdout.write(f"  Archivos referenciados en BD: {len(referenced_files)}")

        self.stdout.write("Escaneando archivos en MEDIA_ROOT...")
        media_files = self._get_media_files(exclude_dirs)
        self.stdout.write(f"  Archivos en disco: {len(media_files)}")

        orphan_files = media_files - referenced_files
        self.stdout.write(f"  Archivos huérfanos: {len(orphan_files)}")

        if not orphan_files:
            self.stdout.write(self.style.SUCCESS("No se encontraron archivos huérfanos."))
            return

        total_size = 0
        deleted = 0
        errors = 0

        for rel_path in sorted(orphan_files):
            full_path = os.path.join(media_root, rel_path)
            try:
                file_size = os.path.getsize(full_path)
            except OSError:
                file_size = 0

            total_size += file_size
            size_str = self._human_size(file_size)

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] {rel_path} ({size_str})")
            else:
                try:
                    os.remove(full_path)
                    deleted += 1
                    self.stdout.write(f"  [ELIMINADO] {rel_path} ({size_str})")
                except OSError as e:
                    errors += 1
                    self.stderr.write(f"  [ERROR] {rel_path}: {e}")

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Total archivos huérfanos: {len(orphan_files)}")
        self.stdout.write(f"Espacio total: {self._human_size(total_size)}")

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY-RUN] No se eliminaron archivos"))
        else:
            self.stdout.write(f"Eliminados: {deleted}")
            if errors:
                self.stdout.write(self.style.ERROR(f"Errores: {errors}"))
            self._clean_empty_dirs(media_root, exclude_dirs)
            self.stdout.write(self.style.SUCCESS("Limpieza completada"))

    def _clean_empty_dirs(self, media_root, exclude_dirs):
        """Elimina directorios vacíos después de borrar archivos."""
        removed = 0
        for root, dirs, files in os.walk(media_root, topdown=False):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            if root == media_root:
                continue
            if not os.listdir(root):
                os.rmdir(root)
                removed += 1
        if removed:
            self.stdout.write(f"Directorios vacíos eliminados: {removed}")

    @staticmethod
    def _human_size(size_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
