# encoding: utf-8
"""Sonda de cobertura por rol: quién ejecutó qué, medido en vez de declarado.

`annotate_coverage()` responde «¿alguna prueba nombra esta ruta?». La pregunta que
importa es otra: **¿con qué rol se ejecutó?** Y esa no se puede contestar leyendo el
texto de las pruebas, porque el rol no está escrito ahí: está en la sesión con la que
corre cada petición.

La alternativa sería que cada prueba declarase lo que ejercita (`covers = [...]`). Se
descartó: son 1 271 pruebas que anotar, declara una intención que nadie garantiza, y es
otra lista paralela — exactamente lo que le pasó a `URLNAME_PERMISSIONS`. Aquí no se
escribe una lista, se observa lo que ocurre.

**La regla que da todo el valor:**

    Una petición ejecutada por un superusuario NO cuenta como cobertura de ningún rol.

`ProfileMiddleware` se salta a los superusuarios (`authentication/middleware.py:49-50`) y
`has_perm` cortocircuita antes de mirar backends. Una prueba que corre con superusuario
ejercita la interacción, no el permiso. Como casi todas las bases Selenium hacen
`force_login(pk=1)` sobre un superusuario, esa regla convierte una sospecha conocida en
un número.

Cómo se enciende:

    ORGANILAB_FEATURE_PROBE=1 python manage.py test ...

o directamente `make feature-coverage`. Apagada, `FeatureProbeMiddleware` no hace nada
más que llamar al siguiente eslabón.

Por qué funciona sin tocar ninguna prueba: `django.test.Client` recorre la cadena
completa de middleware, y `StaticLiveServerTestCase` levanta el servidor **en el mismo
proceso** con el mismo `MIDDLEWARE`. Las 213 pruebas Selenium alimentan la sonda sin que
haya que modificar una sola línea.
"""

import json
import os
import threading
from pathlib import Path

from django.conf import settings

#: Nombre de la variable que enciende la sonda.
ENV_FLAG = "ORGANILAB_FEATURE_PROBE"

#: Pseudo-rol con el que se marcan las peticiones que no prueban ningún permiso.
SUPERUSER = "superusuario"
ANONYMOUS = "anonimo"

#: El id de la prueba en curso, puesto por `ProbeTestRunner`. Es un `local` de hilo
#: porque el servidor de `StaticLiveServerTestCase` atiende en un hilo distinto del que
#: corre la prueba; ahí el valor no llega y se registra `None`, que es honesto.
_state = threading.local()

_TYPE_IN_ORGANIZATION = {
    1: "org_administrator",
    2: "org_lab_manager",
    3: "org_lab_user",
}


def is_enabled():
    return os.environ.get(ENV_FLAG) == "1"


def output_dir():
    path = Path(getattr(settings, "BASE_DIR")).parent / "roadmap" / ".feature_probe"
    path.mkdir(parents=True, exist_ok=True)
    return path


def set_current_test(test_id):
    _state.test_id = test_id


def get_current_test():
    return getattr(_state, "test_id", None)


def _roles_for(request):
    """Los `Rol` que el usuario tiene **en el ámbito de esta URL**.

    Usa el mismo `Q` que `ProfileMiddleware` para autorizar
    (`auth_and_perms/organization_utils.profile_permission_scope_query`): si midiéramos
    con otro ámbito, el informe hablaría de un sistema que no existe.
    """
    from auth_and_perms.models import ProfilePermission
    from auth_and_perms.organization_utils import profile_permission_scope_query
    from laboratory.models import OrganizationStructure

    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return [ANONYMOUS]
    if user.is_superuser:
        return [SUPERUSER]

    profile = getattr(user, "profile", None)
    if profile is None:
        return []

    kwargs = {}
    if request.resolver_match is not None:
        kwargs = request.resolver_match.kwargs or {}
    org_pk = kwargs.get("org_pk") or request.GET.get("org_pk")
    lab_pk = kwargs.get("lab_pk") or request.GET.get("lab_pk")

    query = profile_permission_scope_query(profile, user, lab_pk=lab_pk)
    if org_pk:
        org = OrganizationStructure.objects.filter(pk=org_pk).first()
        if org is not None:
            query |= profile_permission_scope_query(
                profile, user, org_pk=org_pk,
                effective_org=org.get_effective_org_for_profile(profile),
                include_profile=False,
            )

    names = (
        ProfilePermission.objects.filter(query)
        .values_list("rol__name", flat=True)
        .distinct()
    )
    return sorted({name for name in names if name})


def _membership_for(request, org_pk):
    """El `type_in_organization`, que no concede permisos pero sí elegibilidad."""
    from laboratory.models import UserOrganization

    if not org_pk:
        return None
    row = (
        UserOrganization.objects.filter(user=request.user, organization__pk=org_pk)
        .values_list("type_in_organization", flat=True)
        .first()
    )
    return _TYPE_IN_ORGANIZATION.get(row)


class FeatureProbeMiddleware:
    """Anota cada petición: qué ruta, qué método, qué resultado y con qué roles.

    Va **al final** de `MIDDLEWARE`, después de `ProfileMiddleware`, para observar el
    resultado real: los 403 y los 404 son parte de la medición, no ruido. Una ruta que
    solo se ha visitado con 403 no está cubierta para ese rol, está *denegada*, y es una
    información distinta y útil.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = is_enabled()
        self._handle = None

    def __call__(self, request):
        response = self.get_response(request)
        if self.enabled:
            try:
                self._record(request, response)
            except Exception:
                # La sonda jamás puede tumbar una prueba: mide, no participa.
                pass
        return response

    def _record(self, request, response):
        match = getattr(request, "resolver_match", None)
        if match is None or not match.view_name:
            return

        kwargs = match.kwargs or {}
        org_pk = kwargs.get("org_pk") or request.GET.get("org_pk")
        user = getattr(request, "user", None)
        authenticated = bool(user is not None and user.is_authenticated)

        entry = {
            "urlname": match.view_name,
            "method": request.method,
            "status": getattr(response, "status_code", None),
            "user": user.pk if authenticated else None,
            "username": user.get_username() if authenticated else None,
            "roles": _roles_for(request),
            "membership": _membership_for(request, org_pk) if authenticated else None,
            "org_pk": str(org_pk) if org_pk else None,
            "test": get_current_test(),
        }
        self._write(entry)

    def _write(self, entry):
        if self._handle is None:
            path = output_dir() / ("probe-%d.jsonl" % os.getpid())
            self._handle = open(path, "a", encoding="utf-8")
        self._handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._handle.flush()


from django.test.runner import DiscoverRunner  # noqa: E402


class ProbeRunner(DiscoverRunner):
    """Un runner que le pone nombre a cada petición: la prueba que la provocó.

    Se instala con `TEST_RUNNER` en `test_settings`. Con la sonda apagada es el runner
    de Django sin cambios. Con `--parallel` cada trabajador es un proceso aparte con su
    propio fichero, y el id de la prueba puede venir vacío: la atribución por rol sigue
    siendo correcta, solo se pierde el «quién lo provocó».
    """

    def get_resultclass(self):
        base = super().get_resultclass()
        if not is_enabled():
            return base

        import unittest

        parent = base or unittest.TextTestResult

        class Result(parent):
            def startTest(self, test):
                set_current_test(test.id())
                return super().startTest(test)

            def stopTest(self, test):
                outcome = super().stopTest(test)
                set_current_test(None)
                return outcome

        return Result
