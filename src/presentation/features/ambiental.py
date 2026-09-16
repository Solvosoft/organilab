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
    Feature(
        id="AMB-02",
        name="Registrar el consumo de un edificio",
        module="ambiental",
        kind="ui",
        description=(
            "Se elige el edificio, luego el punto de medición y se registra el período "
            "facturado con su cantidad, costo y recibo. El recurso del punto decide la "
            "unidad y los campos extra; un período que se traslapa con otro registro del "
            "mismo punto se rechaza para no duplicar el consumo."
        ),
        priority="P2",
        states=(
            "ConsumptionRecord.is_deleted: False → True (papelera de la organización)",
        ),
        steps=(
            Step(
                id="registrar_consumo",
                name="Registrar, corregir o retirar el consumo de un período",
                actors=ADMIN_AMBIENTAL + ("registro_ambiental",),
                routes=("ambiental:consumptionrecord_list",),
                permissions=("ambiental.view_consumptionrecord",),
                source="src/ambiental/views.py consumptionrecord_list, "
                       "src/ambiental/api/viewsets.py ConsumptionRecordViewSet",
            ),
        ),
    ),
    Feature(
        id="AMB-03",
        name="Definir los m² y las personas de cada edificio por año",
        module="ambiental",
        kind="ui",
        description=(
            "Los denominadores de los indicadores. Se precargan con el área del edificio y "
            "las jornadas de sus zonas de riesgo, y se corrigen a mano; la precarga nunca "
            "pisa un valor escrito por una persona. Un año sin base hereda el anterior."
        ),
        priority="P3",
        steps=(
            Step(
                id="gestionar_bases",
                name="Consultar, precargar y corregir las bases de normalización",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:normalizationbase_list",),
                permissions=("ambiental.view_normalizationbase",),
                source="src/ambiental/views.py normalizationbase_list, "
                       "src/ambiental/normalization.py preload_bases",
            ),
        ),
    ),
    Feature(
        id="AMB-04",
        name="Reportar el consumo: detalle, consolidado y costos",
        module="ambiental",
        kind="ui",
        description=(
            "Los reportes de consumo por edificio, recurso y período, en pantalla, PDF u "
            "hoja de cálculo, sobre la cola de reportes de `report`. El consolidado suma "
            "por mes facturado (`period_end`) y separa unidades distintas."
        ),
        priority="P2",
        steps=(
            Step(
                id="reportes_consumo",
                name="Pedir el reporte de detalle, consolidado o costos",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:report_consumption_detail",
                        "ambiental:report_consumption_summary",
                        "ambiental:report_consumption_cost"),
                permissions=("ambiental.view_consumptionrecord", "laboratory.do_report"),
                source="src/ambiental/views.py AmbientalReportView, src/ambiental/reports.py",
            ),
        ),
    ),
)
