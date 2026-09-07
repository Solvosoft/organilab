# encoding: utf-8
"""Guardianes del catálogo de funcionalidades.

El catálogo tiene un dato que no se puede deducir del código —qué rol ejecuta cada
paso— y por eso existe. Pero todo lo demás que declara *sí* se puede contrastar, y si no
se contrasta acaba como `URLNAME_PERMISSIONS`: 69 claves fantasma y 190 nombres reales
que le faltan, porque durante años nadie comparó la lista con el resolutor.

Estas pruebas son ese contraste. La más importante es
`test_los_permisos_declarados_son_los_que_la_vista_exige`: ata el documento a un
atributo del código, de modo que cambiar un `permission_required` obliga a revisar los
actores del paso.
"""

from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase

from presentation import feature_catalog as fc
from presentation.features import CATALOG_EXCLUDES, PENDING_NAMESPACES
from presentation.role_catalog import ALL_ROLES, CANONICAL_ROLES
from presentation.url_inventory import annotate_coverage, build_inventory

#: Trinquete: solo puede bajar. Cada app que se cataloga sale de `PENDING_NAMESPACES` y
#: baja este techo en el mismo commit.
MAX_PENDING_NAMESPACES = 2

#: Solo puede subir.
MIN_FEATURES = 44


class FeatureCatalogTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.entries = annotate_coverage(build_inventory())
        cls.features = fc.load_catalog()

    def test_no_hay_urlnames_fantasma(self):
        """Cada ruta citada por el catálogo existe en el resolutor.

        Es literalmente el invariante que a `URLNAME_PERMISSIONS` le habría ahorrado sus
        69 claves muertas.
        """
        phantom = fc.phantom_routes(self.entries, self.features)
        self.assertEqual(
            [], phantom,
            "el catálogo cita rutas que no existen: %s" % ", ".join(phantom),
        )

    def test_ninguna_ruta_navegable_queda_huerfana(self):
        """Toda ruta que un usuario alcanza pertenece a una funcionalidad.

        O está en `CATALOG_EXCLUDES` con su motivo, o su app está en
        `PENDING_NAMESPACES` a la espera de su fase. Sin una de las tres cosas, hay una
        parte del software que nadie ha descrito.
        """
        orphans = [entry.full_name for entry in fc.orphan_routes(self.entries, self.features)]
        self.assertEqual(
            [], orphans,
            "rutas navegables sin funcionalidad: %s.\nDeclaralas en "
            "src/presentation/features/ o justificalas en CATALOG_EXCLUDES."
            % ", ".join(sorted(orphans)),
        )

    def test_toda_funcionalidad_declara_actores(self):
        """Sin actor no hay funcionalidad: es la pregunta que motiva el catálogo."""
        for feature in self.features:
            with self.subTest(feature=feature.id):
                self.assertTrue(feature.steps, "%s no tiene pasos" % feature.id)
                for step in feature.steps:
                    self.assertTrue(
                        step.actors,
                        "%s/%s no declara ningún actor" % (feature.id, step.id),
                    )

    def test_todo_actor_existe_en_el_eje_de_roles(self):
        known = {role.id for role in ALL_ROLES}
        for feature in self.features:
            for step in feature.steps:
                for actor in step.actors:
                    with self.subTest(feature=feature.id, actor=actor):
                        self.assertIn(
                            actor, known,
                            "%s/%s cita un rol que no está en role_catalog.py"
                            % (feature.id, step.id),
                        )

    def test_los_permisos_declarados_existen(self):
        for feature in self.features:
            for step in feature.steps:
                for codename in step.permissions:
                    with self.subTest(feature=feature.id, permiso=codename):
                        app_label, name = codename.split(".", 1)
                        self.assertTrue(
                            Permission.objects.filter(
                                content_type__app_label=app_label, codename=name
                            ).exists(),
                            "%s no existe en la base" % codename,
                        )

    def test_los_permisos_declarados_son_los_que_la_vista_exige(self):
        """El catálogo no puede decir que un paso exige algo que la vista no exige.

        Este es el anti-podredumbre fuerte: ata la prosa a un atributo del código. Si
        alguien relaja un `permission_required`, esta prueba falla y obliga a mirar los
        actores del paso — que es exactamente la revisión que hace falta.
        """
        by_name = {entry.full_name: entry for entry in self.entries}
        for feature in self.features:
            for step in feature.steps:
                if not step.permissions:
                    continue
                real = set()
                for route in step.routes:
                    entry = by_name.get(route)
                    if entry is not None:
                        real |= set(getattr(entry, "permissions", ()) or ())
                inspectable = any(
                    by_name[route].category != "infra"
                    for route in step.routes if route in by_name
                )
                with self.subTest(feature=feature.id, step=step.id):
                    if not real:
                        # Declarar un permiso que ninguna vista del paso exige es peor
                        # que no declarar nada: describe un control que no existe. Si
                        # las vistas no exigen nada, el paso debe decirlo con
                        # `permissions=()` y dejar el porqué en `notes`.
                        self.assertFalse(
                            inspectable,
                            "%s/%s declara %s, pero ninguna de sus vistas (%s) exige "
                            "ningún permiso legible. O el paso miente, o el control "
                            "falta en el código."
                            % (feature.id, step.id, sorted(step.permissions),
                               ", ".join(step.routes)),
                        )
                        continue
                    self.assertTrue(
                        set(step.permissions) & real,
                        "%s/%s declara %s pero las vistas exigen %s"
                        % (feature.id, step.id, sorted(step.permissions), sorted(real)),
                    )

    def test_los_ids_de_funcionalidad_son_unicos(self):
        ids = [feature.id for feature in self.features]
        self.assertEqual(sorted(set(ids)), sorted(ids), "hay ids repetidos")

    def test_las_excepciones_tienen_motivo_escrito(self):
        """Una excepción sin motivo es un escondite. Misma regla que `OVERRIDES`."""
        for name, motive in CATALOG_EXCLUDES.items():
            with self.subTest(ruta=name):
                self.assertTrue(motive and motive.strip(), "%s sin motivo" % name)
        for namespace, motive in PENDING_NAMESPACES.items():
            with self.subTest(app=namespace):
                self.assertTrue(motive and motive.strip(), "%s sin motivo" % namespace)

    def test_el_catalogo_commiteado_esta_al_dia(self):
        from pathlib import Path

        from django.conf import settings

        path = Path(settings.BASE_DIR).parent / "roadmap" / "INVENTARIO_FUNCIONALIDADES.md"
        if not path.exists():
            self.skipTest("todavía no se generó el catálogo")
        try:
            call_command("feature_catalog", check=str(path), verbosity=0)
        except Exception as exc:  # noqa: BLE001
            self.fail("%s\nRegeneralo con `make feature-catalog`." % exc)

    def test_trinquetes(self):
        """Las dos métricas que solo pueden mejorar."""
        self.assertGreaterEqual(
            len(self.features), MIN_FEATURES,
            "el catálogo encogió: eran %d funcionalidades" % MIN_FEATURES,
        )
        self.assertLessEqual(
            len(PENDING_NAMESPACES), MAX_PENDING_NAMESPACES,
            "creció la lista de apps sin catalogar; solo debería encoger",
        )


class RoleAxisTest(TestCase):
    """El eje de roles no puede separarse de `update_roles.py`, que es la autoridad."""

    def test_todo_rol_canonico_existe_en_update_roles(self):
        from pathlib import Path

        from django.conf import settings

        source = (
            Path(settings.BASE_DIR)
            / "auth_and_perms" / "management" / "commands" / "update_roles.py"
        ).read_text(encoding="utf-8")
        static = (
            Path(settings.BASE_DIR)
            / "auth_and_perms" / "management" / "commands" / "add_static_rol.py"
        ).read_text(encoding="utf-8")
        creation = (
            Path(settings.BASE_DIR)
            / "auth_and_perms" / "views" / "user_org_creation.py"
        ).read_text(encoding="utf-8")
        haystack = source + static + creation

        for role in CANONICAL_ROLES:
            with self.subTest(rol=role.name):
                self.assertIn(
                    role.name, haystack,
                    "%s está en el eje pero no lo crea ni actualiza nadie. O se quitó "
                    "del código y sobra aquí, o se renombró." % role.name,
                )

    def test_los_alias_no_se_solapan(self):
        """Un nombre no puede resolver a dos roles: la atribución sería ambigua."""
        seen = {}
        for role in ALL_ROLES:
            for name in (role.name,) + role.aliases:
                with self.subTest(nombre=name):
                    self.assertNotIn(
                        name, seen,
                        "%r lo reclaman %s y %s" % (name, seen.get(name), role.id),
                    )
                seen[name] = role.id


class RoleCoverageBaselineTest(TestCase):
    """Trinquete de la cobertura por rol.

    La sonda no corre en cada commit —costaría la suite Selenium entera—, así que lo
    que se guarda aquí es su última medición, commiteada en
    `roadmap/cobertura_por_rol.json`. Estas pruebas impiden que ese fichero se
    contradiga con el catálogo o retroceda en silencio.

    Los números de la línea base son, deliberadamente, muy malos: **15 de 18 roles
    canónicos sin ejercitar y 131 pasos que solo corren con superusuario**. Están aquí
    para que solo puedan mejorar.
    """

    #: Solo puede bajar. Cada prueba nueva que ejercite un rol de verdad lo baja.
    MAX_ROLES_SIN_EJERCITAR = 15
    MAX_PASOS_SOLO_SUPERUSUARIO = 131

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import json
        from pathlib import Path

        from django.conf import settings

        path = (
            Path(settings.BASE_DIR).parent / "roadmap" / "cobertura_por_rol.json"
        )
        cls.baseline = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def setUp(self):
        if self.baseline is None:
            self.skipTest("todavía no se corrió `make feature-coverage`")

    def test_la_linea_base_habla_de_los_pasos_que_existen(self):
        """Si se renombra un paso, la medición commiteada deja de aplicarle.

        Sin esto, la línea base seguiría verde describiendo pasos que ya no existen —
        que es como `URLNAME_PERMISSIONS` acabó con 69 claves fantasma.
        """
        real = {
            "%s/%s" % (feature.id, step.id)
            for feature in fc.load_catalog()
            for step in feature.steps
        }
        medidos = set(self.baseline["pasos"])
        self.assertEqual(
            set(), medidos - real,
            "la medición habla de pasos que ya no existen: %s.\nRegeneralá con "
            "`make feature-coverage`." % ", ".join(sorted(medidos - real)),
        )
        self.assertEqual(
            set(), real - medidos,
            "hay pasos nuevos sin medir: %s.\nCorré `make feature-coverage`."
            % ", ".join(sorted(real - medidos)),
        )

    def test_los_roles_medidos_existen_en_el_eje(self):
        conocidos = {role.id for role in ALL_ROLES}
        for role_id in self.baseline["roles_ejercitados"]:
            with self.subTest(rol=role_id):
                self.assertIn(role_id, conocidos)

    def test_la_cobertura_por_rol_no_retrocede(self):
        sin_ejercitar = len(self.baseline["roles_nunca_ejercitados"])
        self.assertLessEqual(
            sin_ejercitar, self.MAX_ROLES_SIN_EJERCITAR,
            "empeoró la cobertura por rol: %d roles canónicos sin ejercitar, eran %d"
            % (sin_ejercitar, self.MAX_ROLES_SIN_EJERCITAR),
        )
        solo_super = sum(
            1 for estado in self.baseline["pasos"].values()
            if estado == "solo superusuario"
        )
        self.assertLessEqual(
            solo_super, self.MAX_PASOS_SOLO_SUPERUSUARIO,
            "más pasos que solo corren con superusuario: %d, eran %d. Una prueba que "
            "usa superusuario no prueba el permiso."
            % (solo_super, self.MAX_PASOS_SOLO_SUPERUSUARIO),
        )
