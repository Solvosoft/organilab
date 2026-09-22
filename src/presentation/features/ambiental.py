# encoding: utf-8
"""Módulo ambiental: consumos y residuos por edificio.

El registro es **por edificio**, que es donde está el medidor y llega el recibo. Cada
consumo cuelga de un punto de medición (medidor, tanque, punto de acopio) asociado a un
edificio; los laboratorios del punto son informativos hasta que exista prorrateo.

Todas las pantallas son `ObjectCRUD` sobre APIs de `BaseViewSetWithLogs`: la vista HTML
solo exige el permiso de consulta y el resto de acciones las controla la API por acción.

**Acceso por edificio.** Un rol ambiental asignado en la organización cubre todos sus
edificios; asignado sobre un edificio (`ProfilePermission` con content type `Buildings`) solo
cubre ese edificio. Todo lo de AMB-01 a AMB-08 se acota con `ambiental.access.BuildingAccess`:
listas, selects, reportes, panel y alertas muestran solo los edificios visibles, y cada cambio
se valida con el rol que la persona tiene en ese edificio.
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
    Feature(
        id="AMB-05",
        name="Comparar edificios y períodos con indicadores normalizados",
        module="ambiental",
        kind="ui",
        description=(
            "El consumo dividido por los m² o las personas del edificio, con la base y el "
            "total crudo a la vista para que el número sea auditable, y la comparación de "
            "un período contra otro con variación absoluta y porcentual. Unidades mezcladas "
            "en un mismo recurso no se suman: se marcan."
        ),
        priority="P2",
        steps=(
            Step(
                id="indicadores",
                name="Pedir el reporte de indicadores o el de comparación entre períodos",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:report_environmental_indicators",
                        "ambiental:report_consumption_comparison"),
                permissions=("ambiental.view_consumptionrecord", "laboratory.do_report"),
                source="src/ambiental/indicators.py, src/ambiental/reports.py",
            ),
        ),
    ),
    Feature(
        id="AMB-06",
        name="Ver el panel ambiental del año",
        module="ambiental",
        kind="ui",
        description=(
            "Tarjetas con el último mes de cada recurso contra el anterior, consumo y costo "
            "mensuales y el ranking de edificios por indicador, filtrables por año, "
            "edificio, recurso y normalizador."
        ),
        priority="P3",
        steps=(
            Step(
                id="panel",
                name="Abrir el panel y filtrarlo",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:ambiental_dashboard",),
                permissions=("ambiental.view_ambiental_dashboard",),
                source="src/ambiental/views.py AmbientalDashboard, src/ambiental/gtcharts.py",
            ),
        ),
    ),
    Feature(
        id="AMB-07",
        name="Registrar y reportar los residuos y sus manifiestos",
        module="ambiental",
        kind="ui",
        description=(
            "Un residuo es un registro de consumo de un punto de acopio: lleva tratamiento, "
            "gestor autorizado, código de residuo y número de manifiesto, con el manifiesto "
            "adjunto. Tiene su propia pantalla, que solo ofrece puntos de residuos, y un "
            "reporte por tipo, tratamiento y gestor para las inspecciones."
        ),
        priority="P2",
        steps=(
            Step(
                id="registrar_residuo",
                name="Registrar la entrega de un residuo con su manifiesto",
                actors=ADMIN_AMBIENTAL + ("registro_ambiental",),
                routes=("ambiental:waste_list",),
                permissions=("ambiental.view_consumptionrecord",),
                source="src/ambiental/views.py waste_list",
            ),
            Step(
                id="reporte_residuos",
                name="Pedir el reporte de residuos y manifiestos",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:report_waste_manifest",),
                permissions=("ambiental.view_consumptionrecord", "laboratory.do_report"),
                source="src/ambiental/reports.py waste_manifest_rows",
            ),
        ),
    ),
    Feature(
        id="AMB-08",
        name="Detectar consumos atípicos y revisarlos",
        module="ambiental",
        kind="ui",
        description=(
            "Una tarea mensual evalúa las reglas de alerta del proceso "
            "`ambiental.consumption`: el último período de cada punto contra su promedio, "
            "contra un umbral o por meses sin registro. Cada alerta avisa al encargado del "
            "edificio y a los responsables de sus laboratorios; quien la atiende la marca "
            "como revisada con una nota."
        ),
        priority="P2",
        steps=(
            Step(
                id="detectar",
                name="Evaluar las reglas de consumo y crear las alertas",
                actors=("administrador_ambiental",),
                routes=(),
                source="src/ambiental/tasks.py check_consumption_anomalies, src/ambiental/alerts.py",
            ),
            Step(
                id="revisar",
                name="Consultar las alertas y marcarlas como revisadas",
                actors=CONSULTA_AMBIENTAL,
                routes=("ambiental:consumptionalert_list",),
                permissions=("ambiental.view_consumptionalert",),
                source="src/ambiental/api/viewsets.py ConsumptionAlertViewSet.review",
            ),
        ),
    ),
    Feature(
        id="AMB-09",
        name="Dar acceso a las personas por edificio",
        module="ambiental",
        kind="ui",
        description=(
            "Asigna a una persona un rol ambiental (administrador, encargado de registro o "
            "analista) sobre un edificio concreto. Quien administra solo un edificio puede dar "
            "acceso a ese edificio y a ningún otro; sacar a la persona de la organización o "
            "borrar el edificio borra sus accesos."
        ),
        priority="P1",
        steps=(
            Step(
                id="acceso_edificios",
                name="Asignar, cambiar o quitar roles ambientales en un edificio",
                actors=("administrador_ambiental", "administrativo_superior"),
                routes=("ambiental:building_access_list",),
                permissions=("ambiental.manage_building_access",),
                source="src/ambiental/api/building_access.py BuildingAccessViewSet",
            ),
        ),
    ),
)
