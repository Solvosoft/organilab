# encoding: utf-8
"""Las funcionalidades declaradas, un módulo por app.

Se parte por app a propósito: el catálogo es prosa sobre flujos, y un único fichero
gigante es exactamente la forma que tenía `URLNAME_PERMISSIONS` cuando dejó de
revisarse. Un fichero por app cabe en un diff y tiene dueño.
"""

from presentation.features import (
    academic, auth_and_perms, laboratory_inventory, laboratory_structure, misc,
    report, reservations, riskmanagement, sga,
)

#: Orden de lectura del catálogo.
FEATURES = ()
for _module in (academic, auth_and_perms, laboratory_inventory,
                laboratory_structure, misc, report, reservations,
                riskmanagement, sga):
    FEATURES += _module.FEATURES

#: Rutas navegables que a propósito no pertenecen a ninguna funcionalidad. **El motivo
#: es obligatorio**: sin él, la excepción no entra. Es la misma regla que `OVERRIDES` en
#: `url_inventory.py`, y por la misma razón: una lista de excepciones sin motivos
#: escritos se convierte en un cementerio donde se esconde lo que nadie quiso mirar.
CATALOG_EXCLUDES = {
    # Vacío. Cuando aparezca la primera excepción de verdad, va aquí **con su motivo
    # escrito**: es la misma regla que `OVERRIDES` en `url_inventory.py`, y por la
    # misma razón. Una lista de excepciones sin motivos se convierte en el sitio donde
    # se esconde lo que nadie quiso mirar.
}

#: Apps todavía sin catalogar, con la fase en la que entran. Mientras un namespace esté
#: aquí, sus rutas no cuentan como huérfanas — pero el guardián sí exige que la lista
#: encoja: cada app que se cataloga sale de aquí y baja el techo de huérfanas.
#:
#: Que esto exista es deliberado: catalogar 380 rutas de golpe produciría un fichero que
#: nadie revisa. Se entrega app por app, y el trinquete impide que la lista crezca.
PENDING_NAMESPACES = {
    "djgentelella": "biblioteca de terceros: sus rutas no son funcionalidades de Organilab",
    "rest_framework": "biblioteca de terceros",
}
