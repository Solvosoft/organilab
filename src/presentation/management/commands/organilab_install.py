# encoding: utf-8
"""Instalador de una instancia de Organilab.

Reúne en un solo sitio la secuencia que deja una base utilizable, para que el
orquestador la invoque **una vez** en vez de que cada réplica del contenedor
corra `migrate` por su cuenta al arrancar.

    python manage.py organilab_install              # instalación nueva
    python manage.py organilab_install --upgrade    # tras cambiar de imagen
    python manage.py organilab_install --dry-run    # solo enumera los pasos

Se apoya en los comandos que ya existían; no reimplementa ninguno.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Step:
    """Un paso del instalador: un comando de management y cuándo corre."""

    def __init__(self, command, args=(), kwargs=None, on_install=True,
                 on_upgrade=True, note=""):
        self.command = command
        self.args = tuple(args)
        self.kwargs = dict(kwargs or {})
        self.on_install = on_install
        self.on_upgrade = on_upgrade
        self.note = note

    def runs_in(self, upgrade):
        return self.on_upgrade if upgrade else self.on_install


# El esquema y el catálogo de permisos van siempre; el resto son semillas.
CORE_STEPS = (
    Step("migrate", kwargs={"interactive": False},
         note="esquema de la base"),
    Step("init_checks",
         note="tabla de caché (si la caché es de base) y componentes SGA"),
    Step("load_urlname_permissions",
         note="grupo RegisterOrganization y catálogo de permisos por vista"),
    Step("load_common_catalogs",
         note="catálogos comunes (unidades, IARC, órganos diana, IDMG)"),
    Step("new_units",
         note="unidad Libra"),
    Step("seed_iper_catalog",
         note="catálogos IPER (INTE T55) y matriz de riesgo"),
    Step("seed_ambiental_catalog",
         note="catálogos del módulo ambiental (recursos, unidades, puntos)"),
    Step("create_pendingtasks_group",
         note="grupo de tareas pendientes"),
    Step("add_pendingtask_permissions_to_roles",
         note="permisos de tareas pendientes sobre los roles que ya existan"),
    Step("setup_sga_view_group",
         note="grupo SGAView"),
    # Escribe en MEDIA. Es idempotente (se salta los que ya existen), pero no
    # hay motivo para recorrer el árbol de estáticos en cada actualización.
    Step("upload_pictograms", on_upgrade=False,
         note="pictogramas SGA y ONU en MEDIA"),
)

# Estos NO van en la ruta por defecto:
#
#   * `update_roles` deja cada rol igual a `auth_and_perms/management/roles.py`:
#     crea los que faltan, y agrega y quita permisos, así que revierte cualquier
#     ajuste manual de esos roles.
#   * `update_roles_permissions` revienta con `Rol.DoesNotExist` si no existe
#     "Estudiante"; corre después de `update_roles`, que lo crea.
#
# Se dejan accesibles con --with-roles.
ROLE_STEPS = (
    Step("update_roles",
         note="roles según auth_and_perms/management/roles.py (revierte ajustes manuales)"),
    Step("update_roles_permissions", kwargs={"noinput": True},
         note="permisos extra del rol Estudiante (falla si el rol no existe)"),
)


class Command(BaseCommand):
    help = ("Deja una instancia de Organilab lista para usarse: migra el esquema y "
            "siembra catálogos, permisos y grupos. Idempotente.")

    def add_arguments(self, parser):
        parser.add_argument(
            "--upgrade",
            action="store_true",
            help="Modo actualización: corre solo lo que hace falta tras cambiar de "
                 "imagen, y omite las semillas de instalación inicial.",
        )
        parser.add_argument(
            "--with-roles",
            action="store_true",
            dest="with_roles",
            help="Corre además los comandos de roles (update_roles y "
                 "update_roles_permissions); ver el comentario de ROLE_STEPS.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Enumera los pasos que correría, sin tocar nada.",
        )

    def handle(self, *args, **options):
        upgrade = options["upgrade"]
        steps = [s for s in CORE_STEPS if s.runs_in(upgrade)]
        if options["with_roles"]:
            steps += [s for s in ROLE_STEPS if s.runs_in(upgrade)]

        mode = "upgrade" if upgrade else "install"
        self.stdout.write(self.style.MIGRATE_HEADING(
            "organilab_install (%s): %d pasos" % (mode, len(steps))))

        for number, step in enumerate(steps, start=1):
            header = "[%d/%d] %s" % (number, len(steps), step.command)
            if step.note:
                header += " — %s" % step.note
            self.stdout.write(self.style.MIGRATE_HEADING(header))

            if options["dry_run"]:
                continue

            try:
                call_command(step.command, *step.args, **step.kwargs)
            except Exception as exc:
                # Relanzado a propósito, y como CommandError para salir con
                # código distinto de cero.
                #
                # Esto corre como un job de Swarm con una compuerta delante
                # (`dbTableAbsent`): si el instalador se tragara el fallo y
                # saliera 0, la compuerta se cerraría igual y el job NO volvería
                # a lanzarse nunca. Un tenant a medio instalar que nadie va a
                # reintentar es peor que uno que falla a la vista.
                raise CommandError(
                    "El paso '%s' falló (%s: %s). No se continúa: el resto de "
                    "pasos asume que este terminó."
                    % (step.command, type(exc).__name__, exc)
                ) from exc

        if options["dry_run"]:
            self.stdout.write("(dry-run: no se ejecutó nada)")
        else:
            self.stdout.write(self.style.SUCCESS(
                "Organilab listo (%s, %d pasos)." % (mode, len(steps))))
