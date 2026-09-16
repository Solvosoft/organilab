# encoding: utf-8
"""Módulo ambiental: consumos y residuos por edificio.

El registro es **por edificio**, que es donde está el medidor y llega el recibo. Cada
consumo cuelga de un punto de medición (medidor, tanque, punto de acopio) asociado a un
edificio; los laboratorios del punto son informativos hasta que exista prorrateo.

Todas las pantallas son `ObjectCRUD` sobre APIs de `BaseViewSetWithLogs`: la vista HTML
solo exige el permiso de consulta y el resto de acciones las controla la API por acción.
"""

from presentation.feature_catalog import Feature, Step

ADMIN_AMBIENTAL = ("administrador_ambiental", "administrativo_superior")
CONSULTA_AMBIENTAL = ADMIN_AMBIENTAL + ("registro_ambiental", "analista_ambiental")

FEATURES = (
    Feature(
        id="AMB-01",
        name="Configurar los puntos de medición de cada edificio",
        module="ambiental",
        kind="ui",
        description=(
            "Se da de alta cada medidor, tanque o punto de acopio con el número que trae "
            "el recibo, el recurso que mide y el edificio al que pertenece. Retirar un "
            "punto lo manda a la papelera de la organización y conserva su historial."
        ),
        priority="P2",
        steps=(
            Step(
                id="gestionar_puntos",
                name="Listar, crear, editar y retirar puntos de medición",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:measurementpoint_list",),
                permissions=("ambiental.view_measurementpoint",),
                source="src/ambiental/views.py measurementpoint_list, "
                       "src/ambiental/api/viewsets.py MeasurementPointViewSet",
            ),
        ),
    ),
)
