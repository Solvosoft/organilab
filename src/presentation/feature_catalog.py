# encoding: utf-8
"""Catálogo de funcionalidades: qué hace el software, en pasos y con actores.

Una **ruta no es una funcionalidad**. `INVENTARIO_URLS.md` sabe que existe
`reservations_management:manage_reservation`; no sabe que aprobar una reserva es el
tercer paso de un flujo que empieza cuando un docente pide un reactivo y termina cuando
alguien recibe la devolución y repone el stock. Esa agrupación —y sobre todo **qué rol
ejecuta cada paso**— es juicio humano: es lo único de este módulo que se escribe a mano.

Todo lo demás se calcula cruzando con `presentation.url_inventory.build_inventory()`:
la categoría de cada ruta, su plantilla, su vista, si alguna prueba la nombra, y —lo que
importa— qué rutas navegables no pertenecen a ninguna funcionalidad.

La lección de `URLNAME_PERMISSIONS` está en el diseño: un catálogo escrito a mano que
nadie contrasta con el código se pudre en las dos direcciones (hoy tiene 69 claves
fantasma y le faltan 190 nombres reales). Por eso cada dato que *puede* contrastarse se
contrasta en `presentation/tests/test_feature_catalog.py`, y los que no —los actores—
son justamente los que justifican que el fichero exista.
"""

from collections import namedtuple

#: Un paso es una acción de usuario identificable, con su actor y su huella en el código.
#:
#: - ``actors``: ids de `presentation.role_catalog`. **Lo único no inferible.**
#: - ``routes``: urlnames con namespace; el guardián comprueba que existan.
#: - ``permissions``: lo que el paso *declara* exigir. El guardián lo contrasta con lo
#:   que la vista exige de verdad: si alguien cambia un `permission_required`, el
#:   catálogo falla y obliga a revisar los actores.
#: - ``transition``: el cambio de estado, cuando lo hay. Es lo que hace verificable que
#:   la cadena de pasos esté completa y no falte un actor por el camino.
Step = namedtuple(
    "Step",
    "id name actors routes permissions transition source",
)
Step.__new__.__defaults__ = ((), (), (), None, "")

#: ``kind``: ``ui`` (el usuario navega), ``celery`` (lo dispara el planificador) o
#: ``api`` (endpoint sin pantalla propia).
Feature = namedtuple(
    "Feature",
    "id name module kind description steps states priority notes doc",
)
Feature.__new__.__defaults__ = ((), (), "P3", (), None)

NAVIGABLE = ("pagina", "parcial", "accion", "json", "ajax", "descarga")


def load_catalog():
    """Todas las funcionalidades declaradas, en orden de módulo."""
    from presentation.features import FEATURES

    return FEATURES


def features_by_route(features=None):
    """``urlname`` -> lista de ``(feature, step)`` que lo usan."""
    index = {}
    for feature in features if features is not None else load_catalog():
        for step in feature.steps:
            for route in step.routes:
                index.setdefault(route, []).append((feature, step))
    return index


def orphan_routes(entries, features=None):
    """Rutas navegables que no pertenecen a ninguna funcionalidad.

    Es la métrica que dice cuánto del software sigue sin describir. Solo puede bajar:
    el guardián lo trinquetea.
    """
    from presentation.features import CATALOG_EXCLUDES, PENDING_NAMESPACES

    claimed = set(features_by_route(features))
    orphans = []
    for entry in entries:
        if entry.category not in NAVIGABLE:
            continue
        if entry.full_name in claimed or entry.full_name in CATALOG_EXCLUDES:
            continue
        if entry.namespace in PENDING_NAMESPACES:
            continue
        orphans.append(entry)
    return orphans


def phantom_routes(entries, features=None):
    """Urlnames citados por el catálogo que no existen en el resolutor.

    El fallo exacto de `URLNAME_PERMISSIONS`. Aquí se detecta el mismo día.
    """
    real = {entry.full_name for entry in entries}
    return sorted(name for name in features_by_route(features) if name not in real)


def coverage(feature, entries_by_name):
    """Cobertura heredada de las rutas del flujo.

    Devuelve ``(tocada, completa, selenium)``. **Es una pista, no una medición**: sale
    de `annotate_coverage`, que solo sabe que alguien escribió el nombre de la ruta en
    un literal. No sabe con qué rol se ejecutó; eso lo mide la sonda.
    """
    routes = [entries_by_name[r] for step in feature.steps for r in step.routes
              if r in entries_by_name]
    if not routes:
        return False, False, False
    tested = [e for e in routes if e.covered_tests]
    return (
        bool(tested),
        len(tested) == len(routes),
        any(e.covered_selenium for e in routes),
    )


def untested_features(features, entries):
    """Las funcionalidades sin ninguna prueba que nombre alguna de sus rutas."""
    by_name = {e.full_name: e for e in entries}
    result = []
    for feature in features:
        touched, _complete, selenium = coverage(feature, by_name)
        if not touched and not selenium:
            result.append(feature)
    return result


def actors_of(feature):
    seen = []
    for step in feature.steps:
        for actor in step.actors:
            if actor not in seen:
                seen.append(actor)
    return seen


def roles_never_exercised(features=None):
    """Roles canónicos que ningún paso del catálogo atribuye a nadie.

    Es el límite superior del hueco: si el catálogo ni siquiera menciona un rol, ninguna
    prueba lo puede estar ejercitando. La medición real —qué rol ejecutó qué petición—
    la da la sonda.
    """
    from presentation.role_catalog import CANONICAL_ROLES

    named = set()
    for feature in features if features is not None else load_catalog():
        named.update(actors_of(feature))
    return [role for role in CANONICAL_ROLES if role.id not in named]


# --------------------------------------------------------------------------
# Cobertura por rol: ingesta de la sonda
# --------------------------------------------------------------------------

#: Un paso puede estar en uno de cuatro estados, y la diferencia importa.
NEVER = "nunca ejercitado"
ONLY_SUPERUSER = "solo superusuario"
ONLY_DENIED = "solo denegado"
EXERCISED = "ejercitado"


def read_probe(directory=None):
    """Lee los JSONL que dejó `presentation.probe`.

    Un fichero por proceso, porque con `--parallel` cada trabajador escribe el suyo.
    """
    import json
    from pathlib import Path

    from django.conf import settings

    if directory is None:
        directory = Path(settings.BASE_DIR).parent / "roadmap" / ".feature_probe"
    directory = Path(directory)
    if not directory.exists():
        return []

    records = []
    for path in sorted(directory.glob("probe-*.jsonl")):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except ValueError:
                    continue
    return records


def observations_by_route(records):
    """``urlname`` -> lo observado: roles canónicos, ruido y códigos de estado.

    Los nombres de rol se traducen por el eje (`role_catalog.resolve_name`), que conoce
    los alias —``Docente`` es ``Profesor``— y devuelve ``None`` para los roles de
    fixture tipo «Gestión de X», que no existen en producción y por tanto no son
    cobertura de nada.
    """
    from presentation.role_catalog import get_role, resolve_name

    def _BY_ID_OR_NAME(name):
        try:
            return get_role(name)
        except LookupError:
            return resolve_name(name)

    index = {}
    for record in records:
        urlname = record.get("urlname")
        if not urlname:
            continue
        bucket = index.setdefault(urlname, {
            "canonical": set(), "pseudo": set(), "fixture": set(),
            "statuses": set(), "tests": set(),
        })
        bucket["statuses"].add(record.get("status"))
        if record.get("test"):
            bucket["tests"].add(record["test"])
        for name in record.get("roles") or []:
            # La sonda emite los pseudo-roles por su id (`superusuario`, `anonimo`);
            # los `Rol` de verdad, por su nombre tal cual está en la base.
            role = _BY_ID_OR_NAME(name)
            if role is None:
                bucket["fixture"].add(name)
            elif role.counts_as_coverage:
                bucket["canonical"].add(role.id)
            else:
                bucket["pseudo"].add(role.id)
        membership = record.get("membership")
        if membership:
            bucket["pseudo"].add(membership)
    return index


def _ok(statuses):
    return any(status is not None and status < 400 for status in statuses)


def step_coverage(step, observed):
    """El estado de un paso y los roles canónicos que lo ejercitaron de verdad."""
    canonical, pseudo, fixture, statuses, tests = set(), set(), set(), set(), set()
    seen = False
    for route in step.routes:
        bucket = observed.get(route)
        if bucket is None:
            continue
        seen = True
        canonical |= bucket["canonical"]
        pseudo |= bucket["pseudo"]
        fixture |= bucket["fixture"]
        statuses |= bucket["statuses"]
        tests |= bucket["tests"]

    if not seen:
        state = NEVER
    elif canonical and _ok(statuses):
        state = EXERCISED
    elif not _ok(statuses):
        state = ONLY_DENIED
    elif "superusuario" in pseudo:
        state = ONLY_SUPERUSER
    else:
        state = ONLY_SUPERUSER if not canonical else EXERCISED
    return {
        "state": state, "canonical": sorted(canonical), "pseudo": sorted(pseudo),
        "fixture": sorted(fixture), "statuses": sorted(s for s in statuses if s),
        "tests": sorted(tests),
    }


def role_coverage(features, records):
    """El informe completo: por paso, por funcionalidad y por rol."""
    from presentation.role_catalog import CANONICAL_ROLES

    observed = observations_by_route(records)
    per_feature, exercised_roles = [], {}
    for feature in features:
        steps = []
        for step in feature.steps:
            result = step_coverage(step, observed)
            # Un paso de Celery no pasa por HTTP: la sonda no puede verlo, y decir que
            # "nunca se ejercitó" sería mentir por omisión del instrumento.
            if not step.routes:
                result["state"] = "fuera del alcance de la sonda"
            for role_id in result["canonical"]:
                exercised_roles.setdefault(role_id, set()).add(
                    "%s/%s" % (feature.id, step.id)
                )
            steps.append((step, result))
        per_feature.append((feature, steps))

    never = [role for role in CANONICAL_ROLES if role.id not in exercised_roles]
    return {
        "features": per_feature,
        "roles_exercised": exercised_roles,
        "roles_never": never,
        "observations": observed,
    }


def declared_but_not_exercised(report):
    """Pares (paso, rol) que el catálogo declara y la sonda nunca vio.

    Es la lista de trabajo: cada línea es una prueba que falta, ya con su rol y su
    escenario escritos.
    """
    gaps = []
    for feature, steps in report["features"]:
        for step, result in steps:
            if not step.routes:
                continue
            missing = [a for a in step.actors if a not in result["canonical"]]
            for actor in missing:
                gaps.append((feature, step, actor, result["state"]))
    return gaps
