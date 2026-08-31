# encoding: utf-8
"""Recorre las vistas navegables con el cliente de pruebas, sin navegador.

Hasta ahora, comprobar que una página abre costaba un test Selenium: arranque de
Chrome, carga de fixtures y unos tres segundos. Aquí cuesta milisegundos, y eso
cambia el reparto: Selenium deja de usarse para *ver* una página y se reserva
para lo que solo él puede hacer —formularios con select2, modales, DataTables,
JS con estado—.

Qué se comprueba y qué no. Esto verifica que la vista **renderiza**: que resuelve
sus objetos, arma su contexto y pinta su plantilla sin reventar. **No** verifica
permisos: el usuario es superusuario a propósito, y `ProfileMiddleware`
(`authentication/middleware.py:50`) se salta a los superusuarios. La
autorización tiene su propia matriz en `laboratory/tests/labview/`.

Nada se salta en silencio. Una ruta que no se puede probar va a `SMOKE_EXCLUDES`
con el motivo escrito, o cuenta contra `expected_skips`; si el presupuesto sube,
la prueba falla y obliga a mirar por qué.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from presentation.url_inventory import build_inventory


class SkipRoute(Exception):
    """La ruta no se puede construir con los datos de esta fixture."""


# Rutas que no tiene sentido visitar aquí, con el motivo. Sin motivo no entra.
SMOKE_EXCLUDES = {
    "auth_and_perms:login_with_bccr": "abre la ventana de firma digital del BCCR",
    "auth_and_perms:change_to_impostor": "suplanta al usuario y rompe la sesión de la corrida",
    "auth_and_perms:remove_impostor": "contrapartida de la suplantación",
}

# Páginas que hoy están rotas, con el diagnóstico. Se asertan al revés: si una
# empieza a responder 200, la prueba falla y obliga a borrarla de aquí. Así la
# lista no se convierte en un cementerio.
KNOWN_BROKEN = {
    "laboratory:furniture_create": (
        "500: furniture_form.html:48 llama {% get_qr_svg_img furniture %} y en la vista "
        "de creación no existe `furniture`; el tag recibe '' y revienta en "
        "get_qr_by_instance (presentation/utils.py:51)"
    ),
    "riskmanagement:risk_report": (
        "NoReverseMatch: report/base_report_organizations.html:97 pide "
        "{% url 'report:report_status' org_pk=... lab_pk=0 %}, pero el patrón que gana el "
        "nombre solo acepta org_pk (report/urls.py:28). Secuela de los nombres duplicados "
        "de report/urls.py:136-137"
    ),
    "riskmanagement:incident_detail": (
        "mismo NoReverseMatch: extiende base_report_organizations.html"
    ),
    "sga:edit_personal": (
        "AttributeError: sga/views/editor.py:256 lee display_label.barcotesthtml sin "
        "comprobar que exista; cualquier DisplayLabel sin código de barras revienta"
    ),
}


def _first_pk(model):
    obj = model._default_manager.first()
    if obj is None:
        raise SkipRoute("no hay filas de %s en la fixture" % model.__name__)
    return obj.pk


class UrlSmokeMixin:
    """Visita cada ruta `pagina` de los namespaces indicados.

    Cada subclase aporta las fixtures de su familia: ninguna fixture cubre las
    172 páginas del proyecto, y forzarlo produciría una fixture monstruosa que
    nadie mantiene.
    """

    namespaces = ()
    # Se resuelven de la fixture en setUp: fijarlos a 1 obliga a que todas las
    # fixtures numeren igual, y no lo hacen.
    org_pk = None
    lab_pk = None
    username = "admin"
    expected_skips = 0
    # Rutas cuyo redirect es la respuesta correcta (p. ej. las que exigen filtro).
    redirect_ok = ()
    # Cómo rellenar un kwarg que el inventario no puede deducir. La clave puede
    # ser "nombre_de_ruta:kwarg" (gana) o solo "kwarg" (vale para toda la clase).
    kwarg_models = {}

    @classmethod
    def setUpTestData(cls):
        cls.inventory = [
            entry for entry in build_inventory()
            if entry.category == "pagina" and entry.namespace in cls.namespaces
        ]

    def setUp(self):
        from laboratory.models import Laboratory, OrganizationStructure

        user = User.objects.filter(username=self.username).first() or User.objects.first()
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
        self.client.force_login(user)
        self.user = user

        # Ni `check_user_access_kwargs_org` (laboratory/utils.py:496) ni
        # `check_user_access_kwargs_org_lab` (:454) exceptúan a los
        # superusuarios: la primera pide pertenencia a la organización y la
        # segunda, además, un Profile con organización efectiva. Sin montar
        # ambas cosas, media app responde 404 y el smoke acabaría midiendo
        # permisos en vez de renderizado, que es justo lo que no le toca.
        from django.contrib.contenttypes.models import ContentType

        from auth_and_perms.models import Profile, ProfilePermission, Rol
        from laboratory.models import UserOrganization

        profile, _ = Profile.objects.get_or_create(user=user)
        user.refresh_from_db()
        roles = list(Rol.objects.all())
        content_type = ContentType.objects.get_for_model(OrganizationStructure)

        for org in OrganizationStructure.objects.all():
            org.users.add(user)
            if not UserOrganization.objects.filter(user=user, organization=org).exists():
                UserOrganization.objects.create(
                    user=user, organization=org,
                    type_in_organization=3, status=True,
                )
            # `get_effective_org_for_profile` (laboratory/models.py:1178) exige
            # un ProfilePermission **con Rol** en la organización: los permisos
            # efectivos vienen del Rol, no de user_permissions.
            # La fixture puede traer ya varios ProfilePermission para el mismo
            # par (perfil, organización): con get_or_create reventaría.
            permission = ProfilePermission.objects.filter(
                profile=profile, content_type=content_type, object_id=org.pk,
            ).first()
            if permission is None:
                permission = ProfilePermission.objects.create(
                    profile=profile, content_type=content_type, object_id=org.pk,
                )
            if roles:
                permission.rol.add(*roles)

        if self.org_pk is None:
            org = OrganizationStructure.objects.first()
            self.org_pk = org.pk if org else None
        if self.lab_pk is None:
            lab = Laboratory.objects.first()
            self.lab_pk = lab.pk if lab else None

    # -- resolución de kwargs ---------------------------------------------

    def resolve_kwargs(self, entry):
        """Rellena los kwargs de la ruta con datos reales de la fixture.

        El inventario ya sabe qué modelo declara cada CBV, así que la mayoría de
        los `<int:pk>` se resuelven solos. Lo que no, se declara aquí.
        """
        values = {}
        for name in entry.kwargs:
            if name == "org_pk":
                values[name] = self.org_pk
            elif name == "lab_pk":
                values[name] = self.lab_pk
            elif name in self.kwarg_models or "%s:%s" % (entry.name, name) in self.kwarg_models:
                label = self.kwarg_models.get("%s:%s" % (entry.name, name)) \
                    or self.kwarg_models[name]
                values[name] = _first_pk(self._model(label))
            elif name in ("pk", "id") and entry.model:
                values[name] = _first_pk(self.model_for(entry))
            else:
                values[name] = self.extra_kwarg(entry, name)
        return values

    @staticmethod
    def _model(label):
        from django.apps import apps

        return apps.get_model(label)

    def model_for(self, entry):
        from django.apps import apps

        return apps.get_model(entry.model)

    def extra_kwarg(self, entry, name):
        """Gancho por familia: cada subclase resuelve los kwargs de su dominio."""
        raise SkipRoute("no sé qué valor dar a '%s'" % name)

    def _get(self, url):
        """GET tolerante: una página rota puede levantar excepción, no devolver 500."""
        try:
            return self.client.get(url)
        except Exception:  # noqa: BLE001 - es justo lo que se está documentando
            return None

    # -- la prueba ---------------------------------------------------------

    def test_paginas_responden(self):
        skipped = []
        checked = 0

        for entry in self.inventory:
            if entry.full_name in SMOKE_EXCLUDES:
                continue
            with self.subTest(ruta=entry.full_name):
                try:
                    kwargs = self.resolve_kwargs(entry)
                    url = reverse(entry.full_name, kwargs=kwargs)
                except SkipRoute as exc:
                    skipped.append("%s: %s" % (entry.full_name, exc))
                    continue
                except NoReverseMatch as exc:
                    skipped.append("%s: no se pudo construir la URL (%s)" % (entry.full_name, exc))
                    continue

                if entry.full_name in KNOWN_BROKEN:
                    response = self._get(url)
                    self.assertNotEqual(
                        200, getattr(response, "status_code", 500),
                        "%s ya responde 200: quitala de KNOWN_BROKEN (%s)"
                        % (entry.full_name, KNOWN_BROKEN[entry.full_name]),
                    )
                    checked += 1
                    continue

                response = self.client.get(url)
                expected = (200, 302) if entry.full_name in self.redirect_ok else (200,)
                # El destino del redirect es lo que explica un 302 inesperado:
                # HandleErrorMiddleware convierte los 403/404 de una petición
                # HTML en un 302 a error_view, y sin verlo parece otra cosa.
                destination = response.get("Location", "") if response.status_code == 302 else ""
                self.assertIn(
                    response.status_code, expected,
                    "%s (%s) respondió %s%s" % (
                        entry.full_name, url, response.status_code,
                        " → %s" % destination if destination else "",
                    ),
                )
                checked += 1

        self.assertGreater(checked, 0, "el smoke no visitó ninguna ruta")
        self.assertLessEqual(
            len(skipped), self.expected_skips,
            "rutas sin poder visitar (%d, presupuesto %d):\n  %s"
            % (len(skipped), self.expected_skips, "\n  ".join(sorted(skipped))),
        )
