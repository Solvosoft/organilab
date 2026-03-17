"""
Comando de gestión para migrar permisos de roles desde una base de datos vieja a la nueva.

Configuración:
  - Editar las variables en la sección CONFIGURACIÓN antes de ejecutar.
  - SOURCE_DB_*: datos de conexión de la BD vieja.
  - SOURCE_ROL_IDS: lista de IDs de Rol en la BD VIEJA. Se migran TODOS sus permisos.
  - EXTRA_SOURCE_ROL_IDS: lista de listas, alineada posicionalmente con SOURCE_ROL_IDS.
      Cada entrada contiene IDs adicionales de roles en la BD VIEJA cuyos permisos
      se fusionan en el mismo rol destino.
      Ejemplo: SOURCE_ROL_IDS[2] = 6 con EXTRA_SOURCE_ROL_IDS[2] = [96]
               → el rol destino recibe los permisos del rol 6 y del rol 96.
      Dejar [] en las posiciones que no necesiten fusión.
  - DEST_ROL_IDS: lista de IDs de Rol en la BD NUEVA que recibirán los permisos.
      Correspondencia posicional con SOURCE_ROL_IDS. Si hay menos entradas (o está
      vacía), se crea un nuevo Rol basado en los datos del rol origen.
  - DEST_ORGANIZATION_ID: PK de OrganizationStructure en la BD NUEVA, usado como
      referencia al crear nuevos roles.

Uso:
  python manage.py migrate_rol_permissions
"""

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.db.models import Q

from auth_and_perms.models import Rol
from laboratory.models import OrganizationStructure

# ---------------------------------------------------------------------------
# CONFIGURACIÓN — editar estos valores antes de ejecutar
# ---------------------------------------------------------------------------

SOURCE_DB_HOST = "127.0.0.1"
SOURCE_DB_PORT = 5432
SOURCE_DB_NAME = "organilabviejo"
SOURCE_DB_USER = "organilab_user"
SOURCE_DB_PASSWORD = "0rg4n1l4b"

# IDs de registros Rol en la BD VIEJA. Se migran TODOS sus permisos.
# Corresponden posicionalmente con DEST_ROL_IDS.
SOURCE_ROL_IDS = [
    1, 3, 6, 7, 8, 18, 29, 96, 52, 141, 101, 5
]

# IDs adicionales de roles en la BD VIEJA cuyos permisos se fusionan en el mismo
# rol destino. Alineado posicionalmente con SOURCE_ROL_IDS.
# Dejar [] donde no haya fusión.
EXTRA_SOURCE_ROL_IDS = [
    [],[],[],[],[],[],[],[4],[101],[],
]

# IDs de registros Rol existentes en la BD NUEVA que recibirán los permisos.
# Correspondencia posicional con SOURCE_ROL_IDS:
#   DEST_ROL_IDS[0]  → recibe los permisos del SOURCE_ROL_IDS[0]
#   DEST_ROL_IDS[1]  → recibe los permisos del SOURCE_ROL_IDS[1]
#   ... si len(DEST_ROL_IDS) < len(SOURCE_ROL_IDS), los roles sobrantes se crean nuevos.
DEST_ROL_IDS = [
   4, 5, 2, 1, 3, 8, 12, 6, 10
]
# PK de OrganizationStructure en la BD NUEVA. Se usa como referencia al crear nuevos Rol.
DEST_ORGANIZATION_ID = 1

# Alias interno — no modificar
_SOURCE_DB_ALIAS = "source_db_migration"

# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = (
        "Migra permisos desde una BD vieja hacia roles de la BD actual. "
        "Editar las variables de configuración al inicio del archivo antes de ejecutar."
    )

    # ------------------------------------------------------------------
    # Registro / limpieza de la conexión origen en Django
    # ------------------------------------------------------------------

    def _register_source_db(self):
        """Registra la BD vieja en settings.DATABASES para poder usar el ORM con .using().
        Parte de la config del 'default' para heredar todas sus claves y sobreescribe
        solo los datos de conexión, evitando errores por claves faltantes.
        """
        import copy
        config = copy.deepcopy(settings.DATABASES["default"])
        config.update({
            "HOST": SOURCE_DB_HOST,
            "PORT": SOURCE_DB_PORT,
            "NAME": SOURCE_DB_NAME,
            "USER": SOURCE_DB_USER,
            "PASSWORD": SOURCE_DB_PASSWORD,
        })
        settings.DATABASES[_SOURCE_DB_ALIAS] = config

    def _unregister_source_db(self):
        settings.DATABASES.pop(_SOURCE_DB_ALIAS, None)

    # ------------------------------------------------------------------
    # Consultas en la BD origen usando el ORM
    # ------------------------------------------------------------------

    def _fetch_source_rol(self, rol_id):
        """Retorna un dict {id, name, color} del rol en la BD vieja, o None si no existe.
        Se usa .values() para seleccionar solo las columnas que existen en el schema viejo,
        evitando errores por columnas añadidas en migraciones posteriores (ej: description).
        """
        return (
            Rol.objects.using(_SOURCE_DB_ALIAS)
            .filter(pk=rol_id)
            .values("id", "name", "color")
            .first()
        )

    def _fetch_source_permissions(self, rol_id):
        """
        Retorna un queryset de Permission de la BD vieja para el rol indicado.
        La identidad de cada permiso viaja como (codename, app_label, model)
        para evitar conflictos de IDs numéricos entre bases de datos.
        """
        return (
            Permission.objects.using(_SOURCE_DB_ALIAS)
            .filter(rol__id=rol_id)
            .select_related("content_type")
            .values_list("codename", "content_type__app_label", "content_type__model")
        )

    def _resolve_dest_permissions(self, source_perms):
        """
        Dado un iterable de (codename, app_label, model) de la BD vieja,
        retorna la lista de objetos Permission equivalentes en la BD nueva.
        """
        if not source_perms:
            return []

        query = Q()
        for codename, app_label, model in source_perms:
            query |= Q(
                codename=codename,
                content_type__app_label=app_label,
                content_type__model=model,
            )
        return list(Permission.objects.filter(query))

    # ------------------------------------------------------------------
    # Lógica principal
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        stats = {
            "permissions_found_source": 0,
            "permissions_matched_dest": 0,
            "roles_updated": 0,
            "roles_created": 0,
            "errors": [],
        }

        self.stdout.write("Registrando conexión a la base de datos origen…")
        self._register_source_db()

        try:
            # Verificar conectividad antes de empezar
            Rol.objects.using(_SOURCE_DB_ALIAS).exists()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"No se pudo conectar a la BD origen: {exc}"))
            self._unregister_source_db()
            return

        try:
            for idx, source_rol_id in enumerate(SOURCE_ROL_IDS):
                self.stdout.write(f"\nProcesando rol origen #{source_rol_id}…")

                source_rol = self._fetch_source_rol(source_rol_id)
                if source_rol is None:
                    msg = f"Rol origen ID {source_rol_id} no encontrado en la BD vieja — omitido."
                    self.stdout.write(self.style.WARNING(f"  {msg}"))
                    stats["errors"].append(msg)
                    continue

                self.stdout.write(f"  Rol encontrado: '{source_rol['name']}'")

                # Obtener todos los permisos del rol principal en la BD vieja.
                source_perms = set(self._fetch_source_permissions(source_rol_id))
                self.stdout.write(f"  Permisos del rol #{source_rol_id}: {len(source_perms)}")

                # Fusionar permisos de roles extra si se configuraron.
                extra_ids = EXTRA_SOURCE_ROL_IDS[idx] if idx < len(EXTRA_SOURCE_ROL_IDS) else []
                for extra_id in extra_ids:
                    extra_perms = set(self._fetch_source_permissions(extra_id))
                    self.stdout.write(f"  Fusionando rol extra #{extra_id}: {len(extra_perms)} permiso(s)")
                    source_perms |= extra_perms

                source_perms = list(source_perms)
                stats["permissions_found_source"] += len(source_perms)
                self.stdout.write(f"  Total permisos a migrar: {len(source_perms)}")

                # Resolver permisos equivalentes en la BD nueva.
                dest_permissions = self._resolve_dest_permissions(source_perms)
                stats["permissions_matched_dest"] += len(dest_permissions)
                self.stdout.write(f"  Permisos resueltos en BD destino: {len(dest_permissions)}")

                if not dest_permissions:
                    self.stdout.write(self.style.WARNING("  Sin permisos para asignar — omitido."))
                    continue

                # Determinar el Rol destino.
                dest_rol = self._get_or_create_dest_rol(idx, source_rol, stats)
                if dest_rol is None:
                    continue

                # Asignar permisos. add() usa INSERT … ON CONFLICT DO NOTHING
                # internamente por la restricción unique de la tabla intermedia.
                try:
                    dest_rol.permissions.add(*dest_permissions)
                    stats["roles_updated"] += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Se asignaron {len(dest_permissions)} permiso(s) "
                            f"al Rol #{dest_rol.pk} '{dest_rol.name}'."
                        )
                    )
                except Exception as exc:
                    msg = f"Error al asignar permisos al Rol #{dest_rol.pk}: {exc}"
                    self.stderr.write(self.style.ERROR(f"  {msg}"))
                    stats["errors"].append(msg)

                # Verificar que el rol destino quedó con exactamente los mismos permisos.
                self._verify_permissions(source_rol_id, source_perms, dest_rol)
        finally:
            self._unregister_source_db()

        self._print_summary(stats)

    def _get_or_create_dest_rol(self, idx, source_rol, stats):
        """Retorna el Rol destino existente o crea uno nuevo basado en el rol origen."""
        if idx < len(DEST_ROL_IDS):
            dest_rol_id = DEST_ROL_IDS[idx]
            try:
                dest_rol = Rol.objects.get(pk=dest_rol_id)
                self.stdout.write(f"  Usando Rol existente #{dest_rol_id} '{dest_rol.name}'.")
                return dest_rol
            except Rol.DoesNotExist:
                msg = (
                    f"Rol destino ID {dest_rol_id} no existe en la BD nueva — "
                    f"se creará uno nuevo."
                )
                self.stdout.write(self.style.WARNING(f"  {msg}"))
                stats["errors"].append(msg)

        # Crear nuevo rol a partir de los datos del origen.
        self.stdout.write(f"  Creando nuevo Rol basado en '{source_rol['name']}'…")
        return self._create_new_rol(source_rol, stats)

    def _create_new_rol(self, source_rol, stats):
        """Crea un nuevo Rol en la BD nueva copiando los datos del rol origen.
        Si ya existe un rol con el mismo nombre, lo reutiliza en lugar de crear uno nuevo.
        """
        existing = Rol.objects.filter(name=source_rol["name"]).first()
        if existing:
            self.stdout.write(
                self.style.WARNING(
                    f"  Ya existe un Rol con el nombre '{existing.name}' (#{existing.pk}) — se reutiliza."
                )
            )
            return existing
        try:
            rol = Rol.objects.create(
                name=source_rol["name"],
                color=source_rol.get("color") or "#AAAAAA",
                description=source_rol.get("description") or "",
            )
            org = OrganizationStructure.objects.get(pk=1)
            org.rol.add(rol)
            stats["roles_created"] += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"  Nuevo Rol #{rol.pk} '{rol.name}' creado y vinculado a "
                    f"OrganizationStructure #{DEST_ORGANIZATION_ID}."
                )
            )
            return rol
        except Exception as exc:
            msg = f"Error al crear el Rol '{source_rol['name']}': {exc}"
            self.stderr.write(self.style.ERROR(f"  {msg}"))
            stats["errors"].append(msg)
            return None

    def _verify_permissions(self, source_rol_id, source_perms, dest_rol):
        """
        Compara los permisos del rol origen (BD vieja) con los del rol destino (BD nueva)
        tras la migración e imprime las diferencias encontradas.
        """
        self.stdout.write(f"\n  Verificando permisos del Rol #{dest_rol.pk} '{dest_rol.name}'…")

        # Conjunto de identidades del origen: (codename, app_label, model)
        source_set = set(source_perms)

        # Conjunto de identidades del destino tras la migración
        dest_set = set(
            dest_rol.permissions.select_related("content_type")
            .values_list("codename", "content_type__app_label", "content_type__model")
        )

        only_in_source = source_set - dest_set
        only_in_dest = dest_set - source_set

        if not only_in_source and not only_in_dest:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✔ Los permisos coinciden exactamente "
                    f"({len(dest_set)} en origen y destino)."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"  ⚠ Diferencias detectadas — origen: {len(source_set)}, "
                f"destino: {len(dest_set)}"
            )
        )

        if only_in_source:
            self.stdout.write(
                self.style.WARNING(
                    f"  Permisos en origen (BD vieja, rol #{source_rol_id}) "
                    f"que NO están en destino ({len(only_in_source)}):"
                )
            )
            for codename, app_label, model in sorted(only_in_source):
                self.stdout.write(f"    - {app_label}.{model} → {codename}")

        if only_in_dest:
            self.stdout.write(
                self.style.WARNING(
                    f"  Permisos extra en destino (Rol #{dest_rol.pk}) "
                    f"que NO estaban en origen — se eliminarán ({len(only_in_dest)}):"
                )
            )
            # Obtener los objetos Permission a eliminar
            extra_query = Q()
            for codename, app_label, model in only_in_dest:
                extra_query |= Q(
                    codename=codename,
                    content_type__app_label=app_label,
                    content_type__model=model,
                )
            extra_permissions = Permission.objects.filter(extra_query)
            dest_rol.permissions.remove(*extra_permissions)
            for codename, app_label, model in sorted(only_in_dest):
                self.stdout.write(f"    - {app_label}.{model} → {codename}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✔ Se eliminaron {len(only_in_dest)} permiso(s) extra del Rol #{dest_rol.pk}."
                )
            )

    def _print_summary(self, stats):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("RESUMEN")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Permisos encontrados en BD origen  : {stats['permissions_found_source']}")
        self.stdout.write(f"  Permisos encontrados en BD destino : {stats['permissions_matched_dest']}")
        self.stdout.write(f"  Roles actualizados                 : {stats['roles_updated']}")
        self.stdout.write(f"  Roles creados                      : {stats['roles_created']}")
        if stats["errors"]:
            self.stdout.write(self.style.WARNING(f"  Advertencias/Errores ({len(stats['errors'])}):"))
            for err in stats["errors"]:
                self.stdout.write(self.style.WARNING(f"    - {err}"))
        else:
            self.stdout.write(self.style.SUCCESS("  Sin errores."))
        self.stdout.write("=" * 60)
