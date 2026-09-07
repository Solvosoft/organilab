# encoding: utf-8
"""Inventario de las rutas del proyecto, clasificadas por lo que son.

Organilab declara más de 300 rutas con nombre repartidas en quince `urls.py`, y
hasta ahora nada decía cuáles son páginas que un navegador visita y cuáles son
endpoints de API, autocompletes, fragmentos AJAX o descargas. Sin esa
distinción no se puede decidir qué merece una prueba Selenium, qué se cubre con
un `client.get()` y qué se prueba con una unitaria.

`URLNAME_PERMISSIONS` no sirve para esto: es un catálogo de permisos escrito a
mano que ya se desincronizó del código en ambas direcciones. Por eso aquí no se
escribe una lista, se recorre el resolutor real y se clasifica con heurísticas.

La cascada de clasificación (la primera que acierta gana) vive en `classify()`.
Lo que no encaje sale como `desconocida`, y hay una prueba que lo prohíbe: la
categoría existe para obligar a decidir, no para esconder casos.
"""

import ast
import inspect
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

# Plantillas raíz que definen una página navegable. Si la cadena de
# `{% extends %}` llega a una de estas, la vista pinta una página completa.
PAGE_BASES = {"base.html", "gentelella/base.html"}

# Bases de documentos: la vista devuelve un PDF, no una página.
PDF_BASES = {
    "report/base_pdf.html",
    "pdf/base_pdf.html",
    "pdf/base_organization_pdf.html",
}

# Módulos que no son de organilab: admin, autenticación de la librería, OIDC.
INFRA_MODULE_PREFIXES = (
    "django.contrib.admin",
    "django.contrib.auth.views",
    "django.views.i18n",
    "django.views.static",
    "mozilla_django_oidc",
    "djgentelella",
    "djreservation",
    "async_notification",
    "django_celery_beat",
    "django_otp",
)

# La documentación de estas rutas ya está en el código; aquí solo se anota por
# qué la heurística no basta. Sin motivo escrito, una excepción no entra.
OVERRIDES = {
    # Fragmentos HTML que no extienden base.html pero que la heurística de
    # plantilla no puede juzgar sola (se inyectan en un modal por AJAX).
    "laboratory:furniture_update": ("parcial", "renderiza laboratory/dataconfig.html, la rejilla del mueble"),
    "riskmanagement:zone_type_add": ("parcial", "formulario embebido en el modal de zona"),
    "riskmanagement:iper_catalog_add": ("parcial", "formulario embebido en el modal de IPER"),
    "sga:index_editor": ("parcial", "editor de pictogramas embebido, sin layout propio"),

    # Generadores de etiqueta: devuelven la imagen o el PDF ya compuesto, sin
    # plantilla que seguir.
    "laboratory:shelfobject_label": ("descarga", "compone la etiqueta del objeto"),
    "laboratory:generate_shelfobject_label": ("descarga", "compone la etiqueta del objeto"),
    "sga:generate_label": ("descarga", "compone la etiqueta SGA"),
    "sga:security_leaf_pdf": ("descarga", "hoja de seguridad en PDF, plantilla sin base"),

    # Sondas y polling: responden texto o JSON, no pantallas.
    "check_ok": ("infra", "healthcheck del sistema"),
    "media": ("infra", "servidor de MEDIA_ROOT; solo se monta con DEBUG=False"),
    "auth_and_perms:check_signature_window_status_register": (
        "json", "polling del estado de la firma digital BCCR"),
}

TEMPLATE_SUFFIX_BY_MRO = (
    ("django.views.generic.list.ListView", "_list"),
    ("django.views.generic.detail.DetailView", "_detail"),
    ("django.views.generic.edit.DeleteView", "_confirm_delete"),
    ("django.views.generic.edit.ModelFormMixin", "_form"),
)

EXTENDS_RE = re.compile(r"""\{%\s*extends\s+["']([^"']+)["']""")

# Las vistas función no declaran `template_name`: pasan el nombre a `render()`,
# a veces por variable local. Barrer todos los literales que acaban en .html es
# más fiable que perseguir la forma exacta de la llamada.
TEMPLATE_LITERAL_RE = re.compile(r"""["']([\w./-]+\.html)["']""")

CATEGORIES = (
    "pagina",
    "parcial",
    "api",
    "autocomplete",
    "ajax",
    "json",
    "descarga",
    "accion",
    "infra",
    "desconocida",
)


@dataclass
class UrlEntry:
    """Una ruta con nombre, con todo lo que hace falta para decidir cómo probarla."""

    name: str
    namespace: str
    pattern: str
    view: str
    source: str
    category: str
    reason: str = ""
    template: str = ""
    kwargs: tuple = ()
    model: str = ""
    duplicated: bool = False
    covered_selenium: bool = False
    covered_tests: bool = False
    #: Permisos que la vista exige, cuando se pueden leer sin ejecutarla. Es lo que
    #: permite contrastar el catálogo de funcionalidades contra el código en vez de
    #: mantener otra lista paralela.
    permissions: tuple = ()

    @property
    def full_name(self):
        return "%s:%s" % (self.namespace, self.name) if self.namespace else self.name

    @property
    def app(self):
        return self.namespace or self.view.split(".")[0]


# --------------------------------------------------------------------------
# Recorrido del resolutor
# --------------------------------------------------------------------------

def _walk(resolver, prefix="", namespaces=(), in_router=False, groups=()):
    """Recorre el árbol de rutas arrastrando namespace, prefijo y kwargs.

    Los kwargs hay que acumularlos por el camino: `org_pk` y `lab_pk` se
    declaran en el `include()` del padre, no en el patrón final, y sin ellos
    `reverse()` no puede construir la URL.
    """
    for pattern in resolver.url_patterns:
        piece = str(getattr(pattern, "pattern", ""))
        own = tuple(getattr(pattern.pattern, "regex", None).groupindex.keys()) \
            if getattr(pattern, "pattern", None) is not None else ()
        if isinstance(pattern, URLResolver):
            namespace = namespaces
            if pattern.namespace:
                namespace = namespaces + (pattern.namespace,)
            # Un DefaultRouter monta sus rutas bajo un resolutor cuyo módulo es
            # el de rest_framework: marcarlo ahorra adivinar después.
            child_router = in_router or _is_router(pattern)
            yield from _walk(pattern, prefix + piece, namespace, child_router,
                             groups + own)
        elif isinstance(pattern, URLPattern) and pattern.name:
            yield pattern, prefix + piece, namespaces, in_router, groups + own


def _is_router(resolver):
    module = getattr(getattr(resolver, "urlconf_module", None), "__module__", "") or ""
    return "rest_framework.routers" in module


def _source_of(callback):
    try:
        file = inspect.getsourcefile(callback)
        line = inspect.getsourcelines(callback)[1]
    except (TypeError, OSError):
        return ""
    if not file:
        return ""
    try:
        file = str(Path(file).relative_to(Path(settings.BASE_DIR).parent))
    except ValueError:
        pass
    return "%s:%s" % (file, line)


def _view_path(callback):
    view_class = getattr(callback, "view_class", None) or getattr(callback, "cls", None)
    target = view_class or callback
    module = getattr(target, "__module__", "")
    name = getattr(target, "__qualname__", getattr(target, "__name__", str(target)))
    return "%s.%s" % (module, name) if module else name


# --------------------------------------------------------------------------
# Clasificación
# --------------------------------------------------------------------------

def _mro_names(view_class):
    return {"%s.%s" % (c.__module__, c.__qualname__) for c in view_class.__mro__}


def _is_ajax(callback):
    """¿La vista está envuelta por el `@ajax` de django_ajax?

    El decorador usa `functools.wraps`, así que `__module__` y `__qualname__`
    mienten: apuntan a la vista original. El *code object* no: sigue siendo el
    del wrapper, definido en `django_ajax/decorators.py`.
    """
    # `@login_required` suele envolver por fuera al `@ajax`, así que hay que
    # bajar por la cadena de `__wrapped__` que deja functools.wraps en vez de
    # mirar solo el envoltorio exterior.
    target, depth = callback, 0
    while target is not None and depth < 6:
        code = getattr(target, "__code__", None)
        if code is not None and code.co_filename.endswith("django_ajax/decorators.py"):
            return True
        target = getattr(target, "__wrapped__", None)
        depth += 1

    view_class = getattr(callback, "view_class", None)
    if view_class is not None:
        return any("django_ajax" in name for name in _mro_names(view_class))
    return False


def _template_candidates(callback):
    """Nombres de plantilla que la vista podría usar.

    Django deriva el nombre por convención cuando la CBV no declara
    `template_name`; aquí se reproduce esa convención en vez de instanciar la
    vista, que necesitaría request y objeto.
    """
    view_class = getattr(callback, "view_class", None)
    if view_class is None:
        return []

    # Las CBV que se construyen en tiempo de ejecución (ObjectView arma cuatro
    # dentro de su __init__) reciben la plantilla por `as_view()`, no como
    # atributo de clase; Django la guarda en `view_initkwargs`.
    initkwargs = getattr(callback, "view_initkwargs", None) or {}
    declared = initkwargs.get("template_name") or getattr(view_class, "template_name", None)
    if declared:
        return [declared]

    model = getattr(view_class, "model", None)
    if model is None:
        queryset = getattr(view_class, "queryset", None)
        model = getattr(queryset, "model", None) if queryset is not None else None
    if model is None:
        return []

    suffix = getattr(view_class, "template_name_suffix", None)
    if not suffix:
        mro = _mro_names(view_class)
        for base, default in TEMPLATE_SUFFIX_BY_MRO:
            if base in mro:
                suffix = default
                break
    if not suffix:
        return []

    meta = model._meta
    return ["%s/%s%s.html" % (meta.app_label, meta.model_name, suffix)]


def _extends_chain(template_name, depth=0):
    """Sube por la cadena de `{% extends %}` y devuelve todos los nombres vistos."""
    if depth > 5 or not template_name:
        return []
    try:
        source = get_template(template_name).template.source
    except (TemplateDoesNotExist, AttributeError, UnicodeDecodeError):
        return []
    seen = [template_name]
    match = EXTENDS_RE.search(source)
    if match:
        seen.extend(_extends_chain(match.group(1), depth + 1))
    return seen


def _source_text(callback):
    target = getattr(callback, "view_class", None) or callback
    try:
        return inspect.getsource(target)
    except (TypeError, OSError):
        return ""


def _decorator_permissions(source):
    """Los permisos de un `permission_required`, esté donde esté el decorador.

    Se parsea con `ast` en vez de con una expresión regular porque el repo lo escribe de
    cuatro formas distintas y una regex acertaría solo en la primera:

    - `@permission_required("app.perm")` sobre una vista función;
    - con una tupla de permisos y repartido en cuatro líneas por el formateo;
    - `@method_decorator(permission_required(...), name="dispatch")` sobre una CBV, que
      es como lo hacen `academic` y buena parte de `laboratory`;
    - anidado dentro de otro decorador.

    Por eso se busca la llamada a `permission_required` **a cualquier profundidad** del
    árbol del decorador, y solo entonces se leen sus literales: así `name="dispatch"` no
    se cuela como si fuera un permiso.
    """
    try:
        tree = ast.parse(textwrap.dedent(source))
    except (SyntaxError, ValueError):
        return []

    found = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for decorator in node.decorator_list:
            for inner in ast.walk(decorator):
                if not isinstance(inner, ast.Call):
                    continue
                target = inner.func
                name = getattr(target, "id", None) or getattr(target, "attr", None)
                if name != "permission_required":
                    continue
                for argument in inner.args:
                    for literal in ast.walk(argument):
                        if isinstance(literal, ast.Constant) and \
                                isinstance(literal.value, str):
                            found.append(literal.value)
        # Solo la definición de más afuera: lo anidado es detalle de implementación.
        break
    return found


def _permissions_of(callback):
    """Los permisos que la vista exige, leídos sin ejecutarla.

    Tres fuentes, por orden de fiabilidad: el atributo `permission_required` de la
    clase (lo que usan las CBV con `PermissionRequiredMixin`), el mismo atributo pasado
    por `as_view()`, y —para las vistas función— el decorador `@permission_required`
    del código fuente.

    Lo que se calcula en tiempo de ejecución queda fuera, y está bien: lo que no es
    literal tampoco es documentable.
    """
    found = []

    def _add(value):
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, (list, tuple, set, frozenset)):
            found.extend(item for item in value if isinstance(item, str))

    view_class = getattr(callback, "view_class", None)
    if view_class is not None:
        _add(getattr(view_class, "permission_required", None))
        initkwargs = getattr(callback, "view_initkwargs", None) or {}
        _add(initkwargs.get("permission_required"))

    if not found:
        # Vista función: el decorador ya envolvió el callable, así que el atributo no
        # existe. `getsource` de un objeto decorado devuelve el fuente con todos sus
        # decoradores, que es justo lo que hace falta.
        found.extend(_decorator_permissions(_source_text(callback)))

    # Un codename sin app no identifica el permiso: hay repetidos entre aplicaciones.
    return tuple(name for name in dict.fromkeys(found) if "." in name)


def classify(callback, full_name, in_router, route=""):
    """Devuelve `(categoria, motivo, plantilla)`. Cascada: el primer acierto gana."""
    module = getattr(callback, "__module__", "") or ""

    if route.startswith("tableapi/"):
        return "autocomplete", "lookup servido bajo /tableapi/", ""
    if full_name.startswith("admin:"):
        return "infra", "administración de Django", ""
    if module.startswith(INFRA_MODULE_PREFIXES):
        return "infra", "vive fuera de organilab (%s)" % module, ""

    if in_router or getattr(callback, "cls", None) is not None:
        return "api", "endpoint DRF", ""
    if ".api." in module or module.endswith(".api"):
        return "api", "módulo de API", ""
    if module.endswith("gtselects") or module.endswith("gtcharts"):
        return "autocomplete", "lookup de djgentelella", ""

    if _is_ajax(callback):
        return "ajax", "envuelta por @ajax de django_ajax", ""

    if full_name in OVERRIDES:
        category, reason = OVERRIDES[full_name]
        return category, reason, ""

    for template in _template_candidates(callback):
        chain = _extends_chain(template)
        if not chain:
            continue
        if PAGE_BASES.intersection(chain):
            return "pagina", "extiende %s" % chain[-1], template
        if PDF_BASES.intersection(chain):
            return "descarga", "extiende una base de PDF", template
        return "parcial", "no llega a base.html (%s)" % " → ".join(chain), template

    source = _source_text(callback)
    partial = ""
    for template in dict.fromkeys(TEMPLATE_LITERAL_RE.findall(source)):
        chain = _extends_chain(template)
        if not chain:
            continue
        if PAGE_BASES.intersection(chain):
            return "pagina", "renderiza %s" % template, template
        if PDF_BASES.intersection(chain):
            return "descarga", "renderiza el PDF %s" % template, template
        partial = partial or template

    if partial:
        return "parcial", "renderiza %s, que no llega a base.html" % partial, partial
    if "FileResponse" in source or "application/pdf" in source or "content_type=" in source:
        return "descarga", "devuelve un fichero", ""
    if "JsonResponse" in source:
        return "json", "devuelve JsonResponse", ""
    if "redirect(" in source or "HttpResponseRedirect" in source:
        return "accion", "acción que redirige", ""
    if "render(" in source:
        return "parcial", "render con plantilla dinámica", ""

    return "desconocida", "la cascada no la reconoció", ""


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------

def build_inventory():
    """Recorre el resolutor y devuelve la lista de `UrlEntry`, ya deduplicada."""
    entries = []
    seen = {}

    for pattern, route, namespaces, in_router, groups in _walk(get_resolver()):
        callback = pattern.callback
        namespace = ":".join(namespaces)
        full_name = "%s:%s" % (namespace, pattern.name) if namespace else pattern.name
        category, reason, template = classify(callback, full_name, in_router, route)

        view_class = getattr(callback, "view_class", None)
        model = ""
        if view_class is not None:
            target = getattr(view_class, "model", None)
            if target is None:
                queryset = getattr(view_class, "queryset", None)
                target = getattr(queryset, "model", None) if queryset is not None else None
            if target is not None:
                model = "%s.%s" % (target._meta.app_label, target._meta.model_name)

        entry = UrlEntry(
            name=pattern.name,
            namespace=namespace,
            pattern="/" + route,
            view=_view_path(callback),
            source=_source_of(callback),
            category=category,
            reason=reason,
            template=template,
            kwargs=tuple(dict.fromkeys(groups)),
            model=model,
            permissions=_permissions_of(callback),
        )

        if full_name in seen:
            # `reverse()` devuelve la última registrada: el nombre repetido es
            # una ruta muerta salvo que ambas apunten al mismo callback.
            previous = seen[full_name]
            benign = previous.view == entry.view
            previous.duplicated = not benign
            entry.duplicated = not benign
        seen[full_name] = entry
        entries.append(entry)

    return entries


def pages(entries=None, namespaces=None):
    """Solo las rutas navegables, opcionalmente filtradas por namespace."""
    entries = build_inventory() if entries is None else entries
    result = [e for e in entries if e.category == "pagina"]
    if namespaces:
        result = [e for e in result if e.namespace in namespaces]
    return result


def annotate_coverage(entries, root=None):
    """Marca cada ruta según aparezca en un `reverse()` de las pruebas.

    Distingue Selenium del resto por la ruta del fichero: es lo que permite ver
    de un vistazo qué se está probando con navegador sin necesitarlo.

    **Es una pista, no una medición.** Solo dice que alguien escribió el nombre
    de la ruta en un literal: no sabe si la prueba asertó nada, si está
    `@skip`, ni —lo que más importa— con qué rol se ejecutó. Para eso está la
    sonda de `presentation/probe.py`, que mide peticiones reales.
    """
    root = Path(root or Path(settings.BASE_DIR))
    # Además de `reverse()`, se reconocen los ayudantes de navegación de las
    # suites Selenium (`navigate("nombre")`, `navigate_to_sga("nombre")`...).
    # Sin esto, un flujo que navegue por nombre a través del ayudante queda
    # contado como "sin prueba" y el inventario subestima la cobertura: es lo
    # que pasaba con las suites de report, sga y las transversales.
    reverse_re = re.compile(
        r"""(?:reverse(?:_lazy)?|navigate(?:_to_[a-z_]+)?)\(\s*["']([^"']+)["']"""
    )
    selenium_names, test_names = set(), set()

    for path in _test_sources(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        found = set(reverse_re.findall(text))
        if "selenium_tests" in str(path):
            selenium_names |= found
        else:
            test_names |= found

    for entry in entries:
        # Con namespace se exige el nombre completo. Casar también por el nombre
        # pelado hacía que un `reverse("index")` de cualquier app marcara como
        # cubierta cualquier ruta llamada `index` de cualquier namespace.
        keys = {entry.full_name} if entry.namespace else {entry.name}
        entry.covered_selenium = bool(keys & selenium_names)
        entry.covered_tests = bool(keys & test_names)
    return entries


def _test_sources(root):
    """Los ficheros de prueba, incluidos los ayudantes que no se llaman `test*`.

    Barrer solo `test*.py` dejaba fuera los `base.py` de las suites Selenium
    —`capacitacion/base.py`, `transversal/base.py`—, que es justamente donde
    viven los `navigate_to_*` con su `reverse()` literal. El resultado eran
    falsos negativos en las rutas que solo se visitan por ayudante.
    """
    seen = set()
    for path in sorted(root.rglob("*.py")):
        text = str(path)
        if "/migrations/" in text:
            continue
        is_test_module = path.name.startswith("test")
        in_test_package = "/tests/" in text or "/tests.py" in text
        if not (is_test_module or in_test_package):
            continue
        if path not in seen:
            seen.add(path)
            yield path


def counts_by_category(entries):
    result = {category: 0 for category in CATEGORIES}
    for entry in entries:
        result[entry.category] = result.get(entry.category, 0) + 1
    return result
