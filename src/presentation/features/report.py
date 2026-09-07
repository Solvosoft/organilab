# encoding: utf-8
"""Reportes: pedirlos, esperarlos y descargarlos.

Veinticuatro rutas y **un solo ciclo**: se rellena un formulario, se encola una tarea,
la pantalla hace polling contra el estado y al final aparece la descarga. Once de las
trece vistas de listado comparten la misma plantilla
(`report/base_report_form_view.html`), así que son la misma funcionalidad con distinto
conjunto de datos, no once funcionalidades — que es exactamente la regla de
`roadmap/ESTRATEGIA_PRUEBAS.md`: *si dos rutas comparten plantilla, comparten
escenario*.

El eje de roles aquí es de dos posiciones, no de dieciocho: `laboratory.view_report`
para ver el catálogo y `laboratory.do_report` para generar y descargar
(`laboratory/models.py:1405-1408`).
"""

from presentation.feature_catalog import Feature, Step

#: Quien puede pedir un reporte. `Regente` está por diseño: su rol es de solo lectura
#: **más** los reportes de regencia y precursores (`update_roles.py:979`).
SOLICITANTES = ("administrativo_superior", "administrador_laboratorio", "regente",
                "asistente_laboratorio", "solo_lectura",
                "administrativo_centro_trabajo")

FEATURES = (
    Feature(
        id="REP-01",
        name="Pedir un reporte, esperar a que se genere y descargarlo",
        module="report",
        kind="ui",
        description=(
            "El ciclo asíncrono común a los dieciséis tipos de reporte: se elige el "
            "laboratorio y el formato, se encola la tarea, el panel consulta el estado "
            "hasta que termina y entonces se abre la tabla o se baja el fichero. Lo "
            "que justifica una prueba de navegador aquí es justamente ese ciclo: no se "
            "puede comprobar con un `client.get()`."
        ),
        states=(
            'TaskReport / DocumentReportStatus: "On hold" → "Generated" → "Delivered" '
            "(`report/models.py:10-18`)",
        ),
        priority="P1",
        doc="docs/source/general_usage/reports.rst",
        steps=(
            Step(
                id="elegir",
                name="Elegir el reporte y sus parámetros",
                actors=SOLICITANTES,
                routes=("report:reports_objects_list",
                        "report:reports_limited_shelf_objects_list",
                        "report:reactive_precursor_object_list",
                        "report:object_change_logs", "report:waste_report",
                        "report:reactive_report", "report:risk_zone_report",
                        "report:reactive_stock_report",
                        "report:reports_furniture_detail",
                        "report:compatibility_report", "report:hazard_map_report",
                        "report:donations_report"),
                permissions=("laboratory.do_report",),
                source="src/report/views/reports_org.py (12 vistas, misma plantilla)",
            ),
            Step(
                id="encolar",
                name="Encolar la generación del reporte",
                actors=SOLICITANTES,
                routes=("report:create_report_request",
                        "report:create_organization_report_request"),
                permissions=("laboratory.do_report",),
                transition='crea TaskReport en "On hold"',
                source="src/report/views/base.py create_request_by_report",
            ),
            Step(
                id="esperar",
                name="Consultar el estado hasta que la tarea termina",
                actors=SOLICITANTES,
                routes=("report:report_status", "report:report_organization_status"),
                permissions=("laboratory.do_report",),
                source="src/report/views/base.py report_status",
            ),
            Step(
                id="ver_tabla",
                name="Abrir el resultado en pantalla",
                actors=SOLICITANTES,
                routes=("report:report_table", "report:report_organization_table"),
                permissions=("laboratory.do_report",),
                source="src/report/views/base.py report_table",
            ),
            Step(
                id="descargar",
                name="Descargar el fichero generado",
                actors=SOLICITANTES,
                routes=("report:generate_report",
                        "report:generate_organization_report"),
                permissions=("laboratory.do_report",),
                transition='"Generated" → "Delivered"',
                source="src/report/views/base.py download_report",
            ),
        ),
        notes=(
            "Dieciséis tipos de reporte por cinco formatos (`html`, `pdf`, `xls`, "
            "`xlsx`, `ods`) declarados en `report/register.py` `REPORT_FORMS`: **80 "
            "combinaciones** que se cubren recorriendo el registro con `subTest`, no "
            "con ochenta escenarios de navegador.",
            "HALLAZGO-REP-1: `TaskReport.STATUS_TEMPLATE` (`report/models.py:10-18`) "
            "usa **cadenas traducidas como claves** de choice: el valor que se "
            "persiste depende del idioma activo de quien genera el reporte.",
            "`report_status` y `report_organization_status` son dos nombres para la "
            "misma URL (`urls.py:21,39`). Es deliberado y benigno: ambos resuelven.",
        ),
    ),
    Feature(
        id="REP-02",
        name="Llevar el control de precursores y presentar su reporte mensual",
        module="report",
        kind="ui",
        description=(
            "Los precursores tienen su propia pantalla y su propio ciclo, con valores "
            "que se registran por periodo. Es obligación regulatoria, no un reporte "
            "más: por eso tiene plantilla propia y una tarea mensual que lo prepara."
        ),
        priority="P1",
        steps=(
            Step(
                id="consultar",
                name="Consultar el reporte de precursores y sus valores",
                actors=SOLICITANTES,
                routes=("report:precursor_report",
                        "report:precursor_report_values_view"),
                permissions=("laboratory.do_report",),
                source="src/report/views/reports_org.py:192 PrecursorsView",
            ),
        ),
    ),
    Feature(
        id="REP-03",
        name="Presentar el reporte de regencia",
        module="report",
        kind="ui",
        description=(
            "El informe propio del Regente Químico, con formulario y plantilla "
            "distintos del resto."
        ),
        priority="P2",
        steps=(
            Step(
                id="regencia",
                name="Generar el reporte de regencia",
                actors=("regente", "administrativo_superior"),
                routes=("report:regency_report",),
                permissions=("laboratory.do_report",),
                source="src/report/views/base.py:529 regency_report",
            ),
        ),
    ),
    Feature(
        id="REP-04",
        name="Ver el mapa de peligros sobre el plano",
        module="report",
        kind="ui",
        description=(
            "La representación visual del riesgo por zona: un plano con la capa de "
            "peligros encima. Es estado en el cliente, y lo único del módulo que se "
            "consulta con `view_report` en vez de `do_report`."
        ),
        priority="P2",
        steps=(
            Step(
                id="mapa",
                name="Abrir el mapa de peligros",
                actors=SOLICITANTES,
                routes=("report:hazard_map_visual",),
                permissions=("laboratory.view_report",),
                source="src/report/views/riskzones.py hazard_map_visual_view",
            ),
        ),
    ),
)
