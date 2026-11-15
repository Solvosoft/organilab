"""Lectura de los Excel de equipos del laboratorio (fase 2 de plans/EQUIPOS_ISO17025_PLAN.md).

Dos formatos, reconocidos por sus encabezados y no por su posición:

* **Inventario** (p. ej. la hoja «Inventario de trabajo asistente»): un renglón de
  encabezados con Equipo, Marca, Modelo, Serie, N° Activo, Código del laboratorio,
  Responsable, Verificación, Ubicación y Placa.
* **Programa de equipos PT-05 R-10**: encabezado de varias filas con celdas combinadas
  (Magnitud, Código, Descripción, Posición, Estado, datos del equipo, características
  metrológicas, responsables, calibración y hasta cuatro bloques de mantenimiento).

El resultado son filas JSON-serializables que se guardan temporalmente y se revisan en
pantalla antes de crear nada. Este módulo no toca la base de datos.
"""
import datetime
import re
import unicodedata

import openpyxl

INVENTORY = "inventory"
PROGRAM = "program"

#: Valores que el laboratorio usa para "no aplica / no indicado".
EMPTY_VALUES = {"", "na", "n/a", "ni", "no indica", "-", "--", "none", "seleccione"}
CHECK_MARKS = {"√", "✓", "✔", "☑"}
CHECKED_WORDS = {"si", "yes", "true", "1"}  # normalizados; «x» y «no» son «no realizado»

INVENTORY_COLUMNS = {
    "name": ("equipo", "nombre del equipo", "nombre"),
    "brand": ("marca", "fabricante"),
    "model": ("modelo",),
    "serial_number": ("serie", "numero de serie", "n de serie"),
    "asset_number": ("n activo", "no activo", "numero de activo", "activo", "patrimonio"),
    "internal_code": ("codigo del laboratorio", "codigo de laboratorio", "codigo interno", "codigo"),
    "responsible": ("responsable", "persona responsable"),
    "notes": ("verificacion", "observaciones", "notas"),
    "physical_location": ("ubicacion", "posicion"),
    "plaque": ("placa",),
}

PROGRAM_COLUMNS = {
    "magnitude": ("magnitud",),
    "internal_code": ("codigo",),
    "name": ("descripcion",),
    "physical_location": ("posicion",),
    "status_text": ("estado del equipo",),
    "brand": ("marca",),
    "model": ("modelo",),
    "serial_number": ("serie",),
    "software_version": ("version del software y firmware", "version del software"),
    "measurement_unit": ("unidad de medida",),
    "resolution": ("resolucion",),
    "working_range": ("intervalo de indicaciones", "rango de trabajo"),
    "responsible": ("persona responsable",),
    "authorized_users": ("usuarios activos",),
    "calibration_date": ("fecha de calibracion",),
    "next_calibration_date": ("fecha de proxima calibracion",),
    "calibration_result": ("resultados",),
}

#: Columnas de cada bloque de mantenimiento del PT-05, en orden.
MAINTENANCE_BLOCK = (
    ("programmed", ("programado",)),
    ("type", ("tipo",)),
    ("inspection", ("inspeccion visual",)),
    ("cleaning", ("limpieza",)),
    ("battery", ("cambio de bateria",)),
    ("painting", ("pintura",)),
    ("greasing", ("engrasado",)),
    ("includes_report", ("incluye reporte",)),
    ("affects_calibration", ("afecta los resultados",)),
    ("damage_details", ("detalles de cualquier dano",)),
)
#: Clave del checklist -> descripción del Catalog ``maintenance_activity``.
ACTIVITY_NAMES = {
    "inspection": "Inspección visual",
    "cleaning": "Limpieza",
    "battery": "Cambio de batería",
    "painting": "Pintura",
    "greasing": "Engrasado",
}


def normalize_label(value):
    """Minúsculas, sin tildes, sin signos y con espacios simples: para comparar encabezados."""
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


#: Los vacíos comparados ya normalizados («N/A» -> "n a», «-» -> "").
EMPTY_NORMALIZED = {normalize_label(value) for value in EMPTY_VALUES}


def clean(value):
    """El valor de una celda listo para JSON; vacío para NA/NI y similares."""
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = " ".join(str(value).split())
    if text in CHECK_MARKS:  # «√» se normaliza a "" (no es ASCII) y no es un vacío
        return text
    if normalize_label(text) in EMPTY_NORMALIZED:
        return ""
    return text


def parse_date(value):
    """Fecha ISO o ``""``. Acepta fechas de Excel y textos dd/mm/aaaa o aaaa-mm-dd."""
    value = clean(value)
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def is_checked(value):
    text = clean(value)
    return text in CHECK_MARKS or normalize_label(text) in CHECKED_WORDS


def merged_value_getter(ws):
    """Lee una celda devolviendo el valor de la combinada que la contiene."""
    anchors = {}
    for merged in ws.merged_cells.ranges:
        value = ws.cell(merged.min_row, merged.min_col).value
        for row in range(merged.min_row, merged.max_row + 1):
            for col in range(merged.min_col, merged.max_col + 1):
                anchors[(row, col)] = value

    def get(row, col):
        if (row, col) in anchors:
            return anchors[(row, col)]
        return ws.cell(row, col).value

    return get


def match_column(label, aliases):
    """``label`` (normalizado) corresponde a alguno de ``aliases``: igual, o lo empieza."""
    for alias in aliases:
        if label == alias or label.startswith(alias + " ") or label.endswith(" " + alias):
            return True
    return False


# --- Inventario -----------------------------------------------------------------------

def find_inventory_header(ws, max_rows=15):
    """``(fila, {campo: columna})`` del encabezado de inventario, o ``(None, {})``."""
    for row in range(1, min(ws.max_row, max_rows) + 1):
        labels = {col: normalize_label(ws.cell(row, col).value) for col in range(1, ws.max_column + 1)}
        columns = {}
        for field, aliases in INVENTORY_COLUMNS.items():
            for col, label in labels.items():
                if label and col not in columns.values() and match_column(label, aliases):
                    columns[field] = col
                    break
        if "name" in columns and "internal_code" in columns:
            return row, columns
    return None, {}


def read_inventory(ws):
    header, columns = find_inventory_header(ws)
    rows = []
    if header is None:
        return rows
    for row in range(header + 1, ws.max_row + 1):
        values = {field: clean(ws.cell(row, col).value) for field, col in columns.items()}
        if not values.get("name") and not values.get("internal_code"):
            continue
        responsible = values.get("responsible", "")
        decommissioned = "retir" in normalize_label(responsible)
        if decommissioned:
            # «Retirada EBC», «DMP RETIRADA 2022-08-08», « Retirado por XVR Resp: DMP»
            responsible = re.sub(r"(?i)retirad[oa]s?|por|resp:?|\d{4}-\d{2}-\d{2}", " ", responsible)
            responsible = " ".join(responsible.split())
        if not values.get("asset_number") and values.get("plaque"):
            values["asset_number"] = values["plaque"]
        rows.append({
            "row": row,
            "internal_code": values.get("internal_code", ""),
            "name": values.get("name", ""),
            "brand": values.get("brand", ""),
            "model": values.get("model", ""),
            "serial_number": values.get("serial_number", ""),
            "asset_number": values.get("asset_number", ""),
            "physical_location": values.get("physical_location", ""),
            "responsible": responsible,
            "notes": values.get("notes", ""),
            "decommissioned": decommissioned,
        })
    return rows


# --- Programa PT-05 R-10 ---------------------------------------------------------------

def find_program_header(ws, max_rows=20, depth=5):
    """``(primera fila de datos, {campo: col}, [bloques de mantenimiento])`` o ``(None, ...)``.

    El encabezado ocupa varias filas con celdas combinadas: cada columna se etiqueta
    con la última celda no vacía de esas filas.
    """
    get = merged_value_getter(ws)
    for top in range(1, min(ws.max_row, max_rows) + 1):
        if normalize_label(get(top, 1)) != "magnitud" and not any(
            normalize_label(get(top, col)) == "codigo" for col in range(1, 4)
        ):
            continue
        labels, paths = {}, {}
        for col in range(1, ws.max_column + 1):
            parts = [normalize_label(get(row, col)) for row in range(top, top + depth)]
            parts = [part for part in parts if part]
            deduped = [part for i, part in enumerate(parts) if i == 0 or part != parts[i - 1]]
            paths[col] = deduped
            labels[col] = deduped[-1] if deduped else ""
        columns = {}
        for field, aliases in PROGRAM_COLUMNS.items():
            for col, label in labels.items():
                if label and col not in columns.values() and match_column(label, aliases):
                    columns[field] = col
                    break
        blocks = []
        for col, label in labels.items():
            if match_column(label, ("programado",)):
                block = {"programmed": col}
                for offset, (key, aliases) in enumerate(MAINTENANCE_BLOCK[1:], start=1):
                    candidate = col + offset
                    if match_column(labels.get(candidate, ""), aliases):
                        block[key] = candidate
                blocks.append(block)
        if "internal_code" in columns:
            data_start = top + depth
            while data_start <= ws.max_row and not ws.cell(data_start, columns["internal_code"]).value:
                data_start += 1
            return data_start, columns, blocks
    return None, {}, []


def read_program(ws):
    start, columns, blocks = find_program_header(ws)
    rows = []
    if start is None:
        return rows
    for row in range(start, ws.max_row + 1):
        values = {field: ws.cell(row, col).value for field, col in columns.items()}
        code = clean(values.get("internal_code"))
        if not code:
            continue
        maintenance = []
        for block in blocks:
            cell = {key: ws.cell(row, col).value for key, col in block.items()}
            programmed = clean(cell.get("programmed"))
            kind = normalize_label(cell.get("type"))
            if not programmed and not kind:
                continue
            maintenance.append({
                "programmed_year": int(programmed) if programmed.isdigit() else None,
                "type": "corrective" if kind.startswith("correct") else "preventive",
                "executed": bool(kind),
                "activities": [name for key, name in ACTIVITY_NAMES.items() if is_checked(cell.get(key))],
                "includes_report": is_checked(cell.get("includes_report")),
                "affects_calibration": is_checked(cell.get("affects_calibration")),
                "damage_details": clean(cell.get("damage_details")) if normalize_label(cell.get("damage_details")) != "no" else "",
            })
        status = normalize_label(values.get("status_text"))
        result = normalize_label(values.get("calibration_result"))
        rows.append({
            "row": row,
            "internal_code": code,
            "name": clean(values.get("name")),
            "magnitude": clean(values.get("magnitude")),
            "physical_location": clean(values.get("physical_location")),
            "status_text": clean(values.get("status_text")),
            "decommissioned": "baja" in status or "retir" in status,
            "brand": clean(values.get("brand")),
            "model": clean(values.get("model")),
            "serial_number": clean(values.get("serial_number")),
            "software_version": clean(values.get("software_version")),
            "measurement_unit": clean(values.get("measurement_unit")),
            "resolution": clean(values.get("resolution")),
            "working_range": clean(values.get("working_range")),
            "responsible": clean(values.get("responsible")),
            "authorized_users": clean(values.get("authorized_users")),
            "calibration_date": parse_date(values.get("calibration_date")),
            "next_calibration_date": parse_date(values.get("next_calibration_date")),
            "calibration_conformity": (
                "conforming" if result == "conforme"
                # «Sujeto a confirmación» no es un resultado: queda sin conformidad y con su texto.
                else "non_conforming" if result == "no conforme" else ""
            ),
            "calibration_result": clean(values.get("calibration_result")),
            "maintenance": maintenance,
        })
    return rows


# --- Libro completo --------------------------------------------------------------------

def detect_sheets(workbook):
    """``[(nombre de hoja, formato, cantidad de filas)]`` de las hojas reconocidas."""
    found = []
    for ws in workbook.worksheets:
        if find_program_header(ws)[0] is not None:
            found.append((ws.title, PROGRAM, len(read_program(ws))))
        elif find_inventory_header(ws)[0] is not None:
            found.append((ws.title, INVENTORY, len(read_inventory(ws))))
    return found


def read_workbook(file, kind, sheet_name=None):
    """Filas del formato ``kind`` en la hoja ``sheet_name`` (o la que más filas tenga)."""
    workbook = openpyxl.load_workbook(file, data_only=True)
    reader = read_program if kind == PROGRAM else read_inventory
    candidates = [
        (title, count) for title, found_kind, count in detect_sheets(workbook) if found_kind == kind
    ]
    if sheet_name:
        candidates = [(title, count) for title, count in candidates if title == sheet_name]
    if not candidates:
        return None, []
    title = max(candidates, key=lambda item: item[1])[0]
    return title, reader(workbook[title])
