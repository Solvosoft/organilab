"""Las acciones que ofrece cada fila de la tabla de objetos, como datos.

Traducción **1:1** de `laboratory/serializers/shelfobject_actions.html`, las 124
líneas de botones condicionados que hoy renderiza el servidor por cada fila.
Cambia de dónde sale la decisión, no cuál es: cada entrada combina el permiso
de Django con el estado del objeto (tipo, si es caja, si tiene contenedor, si
el estante es de descarte) exactamente como lo hace la plantilla.

Un desvío deliberado, anotado: la plantilla comprueba ``{% if shelf.discard %}``
con una variable que **no está en su contexto**, así que esa rama nunca se
ejecuta y hoy un estante de descarte cae al ``elif delete_shelfobject``. Aquí se
usa ``shelfobject.shelf.discard``, que es lo que la plantilla dice querer.

El cliente **no deduce** permisos: pinta lo que este diccionario autoriza. Y
cada endpoint vuelve a exigir el suyo, así que un cliente manipulado no gana
nada saltándose esta capa.
"""

from laboratory.models import Object

#: Acciones que abren otra página en vez de un modal. La biblioteca las declara
#: con ``link: true`` en ``object_actions``.
LINK_ACTIONS = ("log", "maintenance", "report")


def get_shelfobject_actions(user, shelfobject):
    """``{accion: bool}`` para una fila.  Incluye las 13 del inventario."""
    obj_type = shelfobject.object.type
    is_box = bool(shelfobject.is_box)
    is_reactive = obj_type == Object.REACTIVE
    is_material = obj_type == Object.MATERIAL
    is_equipment = obj_type == Object.EQUIPMENT

    can_change = user.has_perm("laboratory.change_shelfobject")
    can_view = user.has_perm("laboratory.view_shelfobject")
    discard_shelf = bool(shelfobject.shelf and shelfobject.shelf.discard)

    return {
        # El ojo de detalle no exige permiso en la plantilla actual.
        "detail": True,
        "labels": is_reactive and user.has_perm("sga.view_recipientsize"),
        "reserve": user.has_perm("reservations_management.add_reservedproducts"),
        "increase": not is_equipment and can_change,
        "decrease": not is_equipment and can_change,
        "transfer_out": user.has_perm("laboratory.add_tranferobject"),
        "log": can_view and user.has_perm("laboratory.view_shelfobjectobservation"),
        # La plantilla ofrece editar reactivos (o su caja) y materiales; los
        # equipos se editan en su propia página, la de mantenimiento.
        "edit": can_change and (is_reactive or is_material),
        "container": can_change and is_reactive and not is_box,
        "move": can_change,
        "maintenance": is_equipment and can_view and can_change,
        "report": user.has_perm("laboratory.do_report"),
        "destroy": (
            user.has_perm("laboratory.can_manage_disposal")
            if discard_shelf
            else user.has_perm("laboratory.delete_shelfobject")
        ),
    }


def get_shelfobject_action_variants(shelfobject):
    """Qué modal corresponde a ``edit`` y a ``move`` para esta fila.

    La plantilla decide entre cuatro formularios de edición y dos de mover
    según el tipo y si es caja.  Es estado del objeto, no permiso, así que
    viaja aparte: la UI elige el modal sin volver a razonar la regla.
    """
    obj_type = shelfobject.object.type
    is_box = bool(shelfobject.is_box)

    if obj_type == Object.REACTIVE:
        edit = "box" if is_box else "reactive"
        move = "plain" if is_box else "container"
    elif obj_type == Object.MATERIAL:
        edit, move = "material", "plain"
    else:
        edit, move = None, "plain"

    return {"edit": edit, "move": move}
