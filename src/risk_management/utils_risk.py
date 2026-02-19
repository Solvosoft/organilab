from django.contrib.contenttypes.models import ContentType
from django.db.models import F

from laboratory.models import ObjectMaximumLimit, Object, Catalog
from report.utils import get_conversion_units_to_kilograms
from typing import List, Dict, Optional, Tuple
import math, json, argparse
import pandas as pd

from risk_management.models import EstablishmentLogs
from sga.models import DangerSubstance, DangerSubstanceCategory, DangerIndication


def get_inventory(filters={}):
    dict_objs = []
    objs_max = ObjectMaximumLimit.objects.filter(**filters)

    objs = Object.objects.filter(
        pk__in=objs_max.values_list("object__pk", flat=True),
    ).distinct()

    process_conditions = Catalog.objects.filter(
        key="process_condition",
    )

    tons_unit = Catalog.objects.get(description="Toneladas")

    for obj in objs:
        data = {}
        total_shelfobjects = 0
        density = getattr(obj.sustancecharacteristics, "density", None)
        units = Catalog.objects.filter(
            pk__in=objs_max.filter(object=obj).values_list(
                "measurement_unit", flat=True
            )
        ).distinct()
        h_codes = [
            h_code
            for h_code in obj.sustancecharacteristics.h_code.values_list(
                "code", flat=True
            )
        ]
        # Extraer los objectos con procesos de condición
        max_objs = ObjectMaximumLimit.objects.filter(
            object=obj,
            measurement_unit__in=units,
            process_condition__in=process_conditions,
        )
        # Se sacan el ultimo registro del objeto deacuerdo a su proceso de condición
        if max_objs.exists():
            for process in process_conditions.filter(
                pk__in=max_objs.values_list("process_condition", flat=True)
            ):
                max_obj = max_objs.filter(process_condition=process).last()
                # Si es un ton, se suma la cantidad
                if max_obj.measurement_unit == tons_unit:
                    total_shelfobjects += objs_max.quantity
                else:
                    # Si no es un ton, se calcula la cantidad de sustancia en kilogramos
                    try:
                        total_shelfobjects += (
                            get_conversion_units_to_kilograms(
                                max_obj.measurement_unit, max_obj.quantity, density
                            )
                            / 1000
                        )
                    except ZeroDivisionError:
                        total_shelfobjects += 0
                data = {
                    "nombre": obj.name,
                    "cas": obj.cas_code,
                    "cantidad_t": total_shelfobjects,
                    "h_codes": ";".join(h_codes),
                    "condicion_proceso": process.description,
                }
        else:
            # Si no se encuentra ningun registro con proceso de condición, se saca el ultimo registro del objeto
            max_obj = ObjectMaximumLimit.objects.filter(
                object=obj, measurement_unit__in=units, process_condition__isnull=True
            ).last()
            if max_obj.measurement_unit == tons_unit:
                total_shelfobjects += max_obj.quantity
            else:
                try:
                    total_shelfobjects += (
                        get_conversion_units_to_kilograms(
                            max_obj.measurement_unit, max_obj.quantity, density
                        )
                        / 1000
                    )
                except ZeroDivisionError:
                    total_shelfobjects += 0

            data = {
                "nombre": obj.name,
                "cas": obj.cas_code,
                "cantidad_t": 0,
                "h_codes": ";".join(h_codes),
                "condicion_proceso": "",
            }
        dict_objs.append(data)

    dataframe = pd.DataFrame(dict_objs)
    dataframe = dataframe.groupby(
        ["nombre", "cas", "condicion_proceso", "h_codes"], as_index=False
    ).agg(cantidad_t=("cantidad_t", "sum"))
    return dataframe


def examples():
    filters = {
        "object__type": 0,
        "laboratory__pk": 54,
        "created_at__year": 2025,
        "object__isnull": False,
        "measurement_unit__isnull": False,
    }
    inv = get_inventory(filters)
    inv = inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])
    danger_substances = list(
        DangerSubstance.objects.all()
        .annotate(
            cas=F("cas_code"),
            umbral_t=F("threshold"),
            tipo_match=F("type_match"),
            nombre_patron=F("patron_name"),
            condiciones_especiales=F("especial_condition"),
            nombre=F("name"),
        )
        .values(
            "nombre",
            "cas",
            "umbral_t",
            "tipo_match",
            "h_codes_match",
            "nombre_patron",
            "condiciones_especiales",
        )
    )
    c3 = cargar_cuadro3(pd.DataFrame(danger_substances))
    danger_categories = list(
        DangerSubstanceCategory.objects.all()
        .annotate(
            h_codes=F("h_code__code"),
            categoria=F("category"),
            seccion=F("section"),
            condicion_proceso=F("process_condition"),
            umbral_t=F("threshold"),
        )
        .values("h_code", "categoria", "seccion", "condicion_proceso", "umbral_t")
    )
    danger_categories_frame = pd.DataFrame(danger_categories)
    danger_categories_frame.rename(
        columns={"h_codes": "h_code"},
    )
    c4 = cargar_umbral_por_H(danger_categories_frame)
    mapH_tipo = cargar_sga_referencia()
    res = clasificar_establecimiento(inv, c3, c4, mapH_tipo)
    with open("zzz-json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)


_MAPA_TIPO_SGA = {
    "peligros físicos": "Físico",
    "peligros para la salud": "Salud",
    "peligros para el medio ambiente": "Ambiental",
}


def cargar_sga_referencia() -> Dict[str, str]:
    danger_indication = list(
        DangerIndication.objects.all()
        .annotate(Codigo_H=F("code"), Tipo=F("danger_type"))
        .values("Codigo_H", "Tipo")
        .distinct()
    )
    df_h = pd.DataFrame(danger_indication)
    df_h["Codigo_H"] = df_h["Codigo_H"].astype(str).str.upper().str.strip()
    df_h["Tipo_normalizado"] = df_h["Tipo"]
    return dict(zip(df_h["Codigo_H"], df_h["Tipo_normalizado"]))


def normalizar_tipo_sga(tipo_raw: str) -> str:
    """Convierte valores del Excel SGA a claves de categoría del Cuadro 4."""
    return _MAPA_TIPO_SGA.get(tipo_raw.strip().lower(), tipo_raw.strip())


def cargar_cas_h(path_csv: str) -> Dict[str, str]:
    df = pd.read_csv(path_csv, dtype=str).fillna("")
    for col in ["cas", "h_codes"]:
        if col not in df.columns:
            raise ValueError("El catálogo CAS→H debe tener columnas: cas, h_codes")
    df["cas"] = df["cas"].str.strip()
    df["h_codes"] = df["h_codes"].astype(str).str.strip()
    return dict(zip(df["cas"], df["h_codes"]))


def cargar_cuadro3() -> pd.DataFrame:
    # df = pd.read_csv(path_csv, dtype=str).fillna("")
    danger_substances = list(
        DangerSubstance.objects.all()
        .annotate(
            cas=F("cas_code"),
            umbral_t=F("threshold"),
            tipo_match=F("type_match"),
            nombre_patron=F("patron_name"),
            condiciones_especiales=F("especial_condition"),
            nombre=F("name"),
        )
        .values(
            "nombre",
            "cas",
            "umbral_t",
            "tipo_match",
            "h_codes_match",
            "nombre_patron",
            "condiciones_especiales",
        )
    )
    df = pd.DataFrame(danger_substances)
    df.rename(
        columns={"h_codes_match": "h_codes"},
    )
    for col in ["cas", "nombre", "umbral_t"]:

        if col not in df.columns:
            raise ValueError("cuadro3.csv debe tener columnas: cas, nombre, umbral_t")
    df["umbral_t"] = pd.to_numeric(df["umbral_t"], errors="coerce").fillna(math.inf)
    df["cas"] = df["cas"].str.strip()
    if "tipo_match" not in df.columns:
        df["tipo_match"] = "cas"
    else:
        df["tipo_match"] = df["tipo_match"].str.strip()
        df.loc[df["tipo_match"] == "", "tipo_match"] = "cas"
    for col in ["h_codes_match", "nombre_patron", "condiciones_especiales"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].astype(str).str.strip()
    return df[
        [
            "cas",
            "nombre",
            "umbral_t",
            "tipo_match",
            "h_codes_match",
            "nombre_patron",
            "condiciones_especiales",
        ]
    ]


def cargar_umbral_por_H() -> pd.DataFrame:
    # df = pd.read_csv(path_csv, dtype=str).fillna("")
    danger_categories = list(
        DangerSubstanceCategory.objects.all()
        .annotate(
            h_codes=F("h_code__code"),
            categoria=F("category"),
            seccion=F("section"),
            condicion_proceso=F("process_condition"),
            umbral_t=F("threshold"),
        )
        .values("h_code", "categoria", "seccion", "condicion_proceso", "umbral_t")
    )
    df = pd.DataFrame(danger_categories)
    df.rename(
        columns={"h_codes": "h_code"},
    )
    for col in ["h_code", "umbral_t", "categoria"]:
        if col not in df.columns:
            raise ValueError(
                "cuadro4_h_umbral.csv debe tener columnas: h_code, umbral_t, categoria"
            )
    df["umbral_t"] = pd.to_numeric(df["umbral_t"], errors="coerce")
    df["h_code"] = df["h_code"].str.strip().str.upper()
    df["categoria"] = df["categoria"].str.strip()  # ya viene normalizada
    if "seccion" in df.columns:
        df["seccion"] = df["seccion"].str.strip().str.upper()
    else:
        df["seccion"] = ""
    if "condicion_proceso" in df.columns:
        df["condicion_proceso"] = df["condicion_proceso"].astype(str).str.strip()
    else:
        df["condicion_proceso"] = ""
    return df


def evaluar_cuadro4_individual(fila, umbral_H_df: pd.DataFrame) -> Dict:
    """
    Paso 4 del Decreto 44741: verifica si UNA sustancia supera algún umbral
    individual del Cuadro 4.  Si cantidad_t >= umbral_t para cualquier match
    → riesgo mayor directo.
    """
    cantidad = fila["cantidad_t"]
    hlist = expandir_hcodes(fila.get("h_codes", ""))
    condicion_sustancia = str(fila.get("condicion_proceso", "")).strip()

    if not hlist or cantidad <= 0:
        return {"supera": False}

    df_match = pd.DataFrame({"h_code": hlist}).merge(
        umbral_H_df, on="h_code", how="inner"
    )
    if df_match.empty:
        return {"supera": False}

    # Resolver condiciones de proceso (misma lógica que contribuciones_por_sustancia)
    filas_resueltas = []
    for h_code, grupo in df_match.groupby("h_code"):
        tiene_condiciones = grupo["condicion_proceso"].str.strip().ne("").any()
        if not tiene_condiciones:
            filas_resueltas.append(grupo)
        elif condicion_sustancia:
            match_cond = grupo[
                grupo["condicion_proceso"].str.strip() == condicion_sustancia
            ]
            if match_cond.empty:
                filas_resueltas.append(grupo.nsmallest(1, "umbral_t"))
            else:
                filas_resueltas.append(match_cond)
        else:
            filas_resueltas.append(grupo.nsmallest(1, "umbral_t"))

    df_resuelto = pd.concat(filas_resueltas, ignore_index=True)

    for _, row in df_resuelto.iterrows():
        if row["umbral_t"] > 0 and cantidad >= row["umbral_t"]:
            return {
                "supera": True,
                "h_code": row["h_code"],
                "umbral": float(row["umbral_t"]),
                "categoria": row["categoria"],
            }

    return {"supera": False}


def clasificar_establecimiento(inventario, c3, umbral_H_df, map_H_to_tipo):
    inv_c3 = evaluar_cuadro3(inventario, c3)

    # Paso 2: verificar Cuadro 3
    if (inv_c3["ratio_c3"] >= 1.0).any():
        detalles = []
        for _, r in inv_c3.iterrows():
            detalles.append(
                {
                    "nombre": r["nombre"],
                    "cas": r["cas"],
                    "cantidad_t": float(r["cantidad_t"]),
                    "nominada_c3": bool(r["nominada_c3"]),
                    "umbral_c3": (
                        None if pd.isna(r["umbral_c3"]) else float(r["umbral_c3"])
                    ),
                    "ratio_c3": (
                        None if pd.isna(r["ratio_c3"]) else float(r["ratio_c3"])
                    ),
                    "h_codes": r["h_codes"],
                    "contribuciones": {},
                    "detalle_contribuciones": [],
                    "regla_cruzada_salud": False,
                }
            )
        return {
            "clasificacion": "riesgo mayor",
            "criterio": "Al menos una sustancia nominada (Cuadro 3) cumple o supera su umbral.",
            "sumatorias_por_categoria": {},
            "detalles": detalles,
            "trazabilidad": {},
        }

    # Paso 4: verificar umbrales individuales de Cuadro 4
    for _, fila in inv_c3.iterrows():
        resultado_c4 = evaluar_cuadro4_individual(fila, umbral_H_df)
        if resultado_c4["supera"]:
            detalles = []
            for _, r in inv_c3.iterrows():
                detalles.append(
                    {
                        "nombre": r["nombre"],
                        "cas": r["cas"],
                        "cantidad_t": float(r["cantidad_t"]),
                        "nominada_c3": bool(r["nominada_c3"]),
                        "umbral_c3": (
                            None if pd.isna(r["umbral_c3"]) else float(r["umbral_c3"])
                        ),
                        "ratio_c3": (
                            None if pd.isna(r["ratio_c3"]) else float(r["ratio_c3"])
                        ),
                        "h_codes": r["h_codes"],
                        "contribuciones": {},
                        "detalle_contribuciones": [],
                        "regla_cruzada_salud": False,
                        "paso4_supera": (
                            r["nombre"] == fila["nombre"] and r["cas"] == fila["cas"]
                        ),
                    }
                )
            return {
                "clasificacion": "riesgo mayor",
                "criterio": (
                    f"Sustancia '{fila['nombre']}' supera umbral individual del Cuadro 4 "
                    f"({resultado_c4['h_code']}: {fila['cantidad_t']}t >= {resultado_c4['umbral']}t)."
                ),
                "sumatorias_por_categoria": {},
                "detalles": detalles,
                "trazabilidad": {},
            }

    # Paso 5: sumatoria por categoría usando Cuadro 4
    sum_por_categoria = {"Físico": 0.0, "Salud": 0.0, "Ambiental": 0.0}
    detalles = []
    advertencias_globales = []

    for _, fila in inv_c3.iterrows():
        res_sust = contribuciones_por_sustancia(fila, umbral_H_df, map_H_to_tipo)

        for cat, val in res_sust["contribuciones"].items():
            if cat in sum_por_categoria:
                sum_por_categoria[cat] += val

        # Propagar advertencias con nombre de sustancia
        for adv in res_sust.get("advertencias", []):
            advertencias_globales.append(f"{fila['nombre']}: {adv}")

        detalles.append(
            {
                "nombre": fila["nombre"],
                "cas": fila["cas"],
                "cantidad_t": float(fila["cantidad_t"]),
                "nominada_c3": bool(fila["nominada_c3"]),
                "umbral_c3": (
                    None if pd.isna(fila["umbral_c3"]) else float(fila["umbral_c3"])
                ),
                "ratio_c3": (
                    None if pd.isna(fila["ratio_c3"]) else float(fila["ratio_c3"])
                ),
                "h_codes": fila["h_codes"],
                "contribuciones": res_sust["contribuciones"],
                "detalle_contribuciones": res_sust["detalle"],
                "regla_cruzada_salud": res_sust["regla_cruzada_salud"],
                "advertencias": res_sust.get("advertencias", []),
            }
        )

    # Redondear sumatorias
    for cat in sum_por_categoria:
        sum_por_categoria[cat] = round(sum_por_categoria[cat], 4)

    criterio = "Sumatoria por categorías SGA (Cuadro 4) "
    if any(v >= 1.0 for v in sum_por_categoria.values()):
        clasif = "riesgo mayor"
        criterio += "≥ 1 en al menos una categoría."
    else:
        clasif = "riesgo menor"
        criterio += "< 1 en todas las categorías."

    return {
        "clasificacion": clasif,
        "criterio": criterio,
        "sumatorias_por_categoria": sum_por_categoria,
        "detalles": detalles,
        "advertencias": advertencias_globales,
        "trazabilidad": {},
    }


def evaluar_cuadro3(inventario: pd.DataFrame, c3: pd.DataFrame) -> pd.DataFrame:
    # Paso A: match por CAS (entradas con tipo_match="cas" y CAS no vacío)
    c3_cas = c3[(c3["tipo_match"] == "cas") & (c3["cas"].str.strip() != "")]
    merged = inventario.merge(c3_cas[["cas", "umbral_t"]], on="cas", how="left")
    merged = merged.rename(columns={"umbral_t": "umbral_c3"})

    # Paso B: match por H-code (entradas con tipo_match="h_categoria")
    c3_hcat = c3[c3["tipo_match"] == "h_categoria"]
    for _, regla in c3_hcat.iterrows():
        h_requeridos = [
            h.strip().upper() for h in regla["h_codes_match"].split(";") if h.strip()
        ]
        umbral = regla["umbral_t"]
        for idx in merged.index:
            h_sustancia = expandir_hcodes(merged.at[idx, "h_codes"])
            if any(h in h_sustancia for h in h_requeridos):
                # Aplicar si no tiene umbral o el nuevo es más bajo
                actual = merged.at[idx, "umbral_c3"]
                if pd.isna(actual) or umbral < actual:
                    merged.at[idx, "umbral_c3"] = umbral

    # Paso C: match por patrón de nombre (entradas con tipo_match="nombre_patron")
    c3_nombre = c3[c3["tipo_match"] == "nombre_patron"]
    for _, regla in c3_nombre.iterrows():
        patrones = [
            p.strip().lower() for p in regla["nombre_patron"].split(";") if p.strip()
        ]
        umbral = regla["umbral_t"]
        for idx in merged.index:
            nombre_sustancia = str(merged.at[idx, "nombre"]).lower()
            if any(patron in nombre_sustancia for patron in patrones):
                actual = merged.at[idx, "umbral_c3"]
                if pd.isna(actual) or umbral < actual:
                    merged.at[idx, "umbral_c3"] = umbral
    merged["nominada_c3"] = ~merged["umbral_c3"].isna()
    merged["ratio_c3"] = merged.apply(
        lambda r: (
            (r["cantidad_t"] / r["umbral_c3"])
            if r["nominada_c3"] and r["umbral_c3"] > 0
            else float("nan")
        ),
        axis=1,
    )
    return merged


# ---------------------------------------------------------------------------
# Expansión de H-codes
# ---------------------------------------------------------------------------


def expandir_hcodes(h_codes_str: str) -> List[str]:
    if not h_codes_str:
        return []
    return [h.strip().upper() for h in h_codes_str.split(";") if h.strip()]


# ---------------------------------------------------------------------------
# Algoritmo por sustancia (no por H-code individual)
# ---------------------------------------------------------------------------


def contribuciones_por_sustancia(
    fila, umbral_H_df: pd.DataFrame, map_H_to_tipo: Dict[str, str]
) -> Dict:
    """
    Calcula las contribuciones de UNA sustancia a cada categoría.
    Retorna dict con:
      - contribuciones: {categoría: valor}
      - detalle: lista de explicaciones
      - regla_cruzada_salud: bool
      - advertencias: lista de advertencias sobre condiciones de proceso
    """
    cantidad = fila["cantidad_t"]
    hlist = expandir_hcodes(fila.get("h_codes", ""))
    condicion_sustancia = str(fila.get("condicion_proceso", "")).strip()
    resultado = {
        "contribuciones": {},
        "detalle": [],
        "regla_cruzada_salud": False,
        "advertencias": [],
    }

    if not hlist or cantidad <= 0:
        return resultado

    # Buscar coincidencias en Cuadro 4
    df_match = pd.DataFrame({"h_code": hlist}).merge(
        umbral_H_df, on="h_code", how="inner"
    )

    if df_match.empty:
        return resultado

    # Resolver condiciones de proceso: para cada h_code, quedarse con una sola fila
    filas_resueltas = []
    advertencias = []
    for h_code, grupo in df_match.groupby("h_code"):
        # pregunta si alguno es true
        tiene_condiciones = grupo["condicion_proceso"].str.strip().ne("").any()
        if not tiene_condiciones:
            # H-code sin condiciones → usar tal cual
            filas_resueltas.append(grupo)
        elif condicion_sustancia:
            # Sustancia especifica condición → filtrar
            match_cond = grupo[
                grupo["condicion_proceso"].str.strip() == condicion_sustancia
            ]
            if match_cond.empty:
                # Condición no encontrada → usar más conservador
                filas_resueltas.append(grupo.nsmallest(1, "umbral_t"))
                advertencias.append(
                    f"{h_code}: condicion '{condicion_sustancia}' no coincide, "
                    f"usando umbral mas bajo ({grupo['umbral_t'].min()}t)"
                )
            else:
                filas_resueltas.append(match_cond)
        else:
            # Sin condición especificada → más conservador + advertencia
            filas_resueltas.append(grupo.nsmallest(1, "umbral_t"))
            advertencias.append(
                f"{h_code}: condicion no especificada, "
                f"usando umbral mas bajo ({grupo['umbral_t'].min()}t)"
            )

    df_match = pd.concat(filas_resueltas, ignore_index=True)

    # Agrupar por categoría → tomar umbral mínimo por categoría
    contribuciones_directas = {}
    detalles = []

    for cat, grupo in df_match.groupby("categoria"):
        umbral_min = grupo["umbral_t"].min()
        if umbral_min > 0:
            contrib = cantidad / umbral_min
            contribuciones_directas[cat] = contrib
            h_usados = ", ".join(grupo["h_code"].tolist())
            notas_usadas = (
                ", ".join(grupo["notas"].tolist()) if "notas" in grupo.columns else ""
            )
            detalle_str = (
                f"{cat}: {cantidad}/{umbral_min} = {contrib:.4f} (H-codes: {h_usados})"
            )
            if notas_usadas:
                detalle_str += f" [{notas_usadas}]"
            detalles.append(detalle_str)

    # Regla de inclusión de Salud (Paso 5, Decreto 44741):
    # Todas las sustancias incluidas en Cuadro 4 deben contribuir a la sumatoria
    # de Salud, independientemente de la sección en que aparezcan.
    if "Salud" not in contribuciones_directas:
        umbral_min_global = df_match["umbral_t"].min()
        if umbral_min_global > 0:
            contrib_salud = cantidad / umbral_min_global
            contribuciones_directas["Salud"] = contrib_salud
            resultado["regla_cruzada_salud"] = True
            h_salud_sga = [h for h in hlist if map_H_to_tipo.get(h) == "Salud"]
            detalles.append(
                f"Salud (inclusión C4): {cantidad}/{umbral_min_global} = {contrib_salud:.4f} "
                f"(H-codes SGA salud: {', '.join(h_salud_sga) if h_salud_sga else 'ninguno'})"
            )

    resultado["contribuciones"] = contribuciones_directas
    resultado["detalle"] = detalles
    resultado["advertencias"] = advertencias
    return resultado


def create_estableshment_logs_data(element, day, labs):
    filters = {
        "object__type": 0,
        "created_at": day,
        "object__isnull": False,
        "measurement_unit__isnull": False,
    }
    if labs.exists():
        filters.update({"laboratory__pk__in": labs})
        inv = get_inventory(filters)
        inv = inv.drop_duplicates(subset=["nombre", "h_codes", "cas", "cantidad_t"])
        c3 = cargar_cuadro3()
        c4 = cargar_umbral_por_H()
        mapH_tipo = cargar_sga_referencia()
        res = json.dumps(
            clasificar_establecimiento(inv, c3, c4, mapH_tipo),
            indent=2,
        )
        ct = ContentType.objects.filter(
            app_label=element._meta.app_label,
            model=element._meta.model_name,
        ).first()
        sumatories = res["sumatorias_por_categoria"]
        EstablishmentLogs.objects.create(
            content_type=ct,
            object_id=element.pk,
            data=res,
            environmental=sumatories["Ambiental"],
            health=sumatories["Salud"],
            physical=sumatories["Físico"],
            establishment_status=res["clasificacion"].capitalize(),
            date=day,
        )
