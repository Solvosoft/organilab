"""Control estadístico de procesos para las cartas de control de equipos (fase 3).

Funciones puras, sin base de datos, sobre ``Decimal``:

* **X̄‑R** (subgrupos de n ≥ 2 lecturas): media y rango de cada subgrupo.
  LC = X̄̄, LCS/LCI = X̄̄ ± A2·R̄. En la carta de rangos: LC = R̄, LCS = D4·R̄, LCI = D3·R̄.
* **I‑MR** (una lectura por registro): el rango móvil es |xᵢ − xᵢ₋₁|.
  LC = X̄, LCS/LCI = X̄ ± E2·MR̄ (E2 = 3/d2 con n = 2). En la carta MR: LCS = D4·MR̄, LCI = 0.

La corrección (p. ej. el error de indicación de las pesas patrón según su certificado) se
resta a cada media antes de comparar o calcular la línea central, igual que el
«promedio corregido» del registro del laboratorio. El rango no cambia con la corrección.

Las constantes son las de la tabla estándar (ASTM E2587 / Montgomery). El método de
control las precarga según n y el laboratorio puede editarlas.
"""
from decimal import ROUND_HALF_UP, Decimal

XBAR_R = "xbar_r"
I_MR = "i_mr"

#: n -> (A2, D3, D4, d2)
CONSTANTS = {
    2: ("1.880", "0", "3.267", "1.128"),
    3: ("1.023", "0", "2.574", "1.693"),
    4: ("0.729", "0", "2.282", "2.059"),
    5: ("0.577", "0", "2.114", "2.326"),
    6: ("0.483", "0", "2.004", "2.534"),
    7: ("0.419", "0.076", "1.924", "2.704"),
    8: ("0.373", "0.136", "1.864", "2.847"),
    9: ("0.337", "0.184", "1.816", "2.970"),
    10: ("0.308", "0.223", "1.777", "3.078"),
}
#: I-MR: rango móvil de 2 lecturas consecutivas.
E2 = Decimal("2.660")
MR_D4 = Decimal("3.267")


def default_constants(chart_type, n):
    """``{"a2", "d3", "d4", "d2"}`` de la tabla estándar para el tipo de carta y n."""
    if chart_type == I_MR:
        return {"a2": E2, "d3": Decimal("0"), "d4": MR_D4, "d2": Decimal("1.128")}
    if n not in CONSTANTS:
        raise ValueError("n must be between 2 and 10 for an X̄-R chart")
    a2, d3, d4, d2 = CONSTANTS[n]
    return {"a2": Decimal(a2), "d3": Decimal(d3), "d4": Decimal(d4), "d2": Decimal(d2)}


def to_decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value).replace(",", "."))


def mean(values):
    values = [to_decimal(value) for value in values]
    return sum(values, Decimal("0")) / len(values)


def subgroup_stats(values, correction=Decimal("0")):
    """``(media, rango, media corregida)`` de las lecturas de un subgrupo."""
    values = [to_decimal(value) for value in values]
    if not values:
        raise ValueError("A subgroup needs at least one reading")
    average = mean(values)
    return average, max(values) - min(values), average - to_decimal(correction)


def moving_ranges(values):
    """|xᵢ − xᵢ₋₁| de una serie (el primero no tiene rango móvil: ``None``)."""
    values = [to_decimal(value) for value in values]
    return [None] + [abs(current - previous) for previous, current in zip(values, values[1:])]


def limits(chart_type, corrected_means, ranges, constants):
    """Límites a partir de un período de referencia.

    ``corrected_means``: la media corregida de cada subgrupo (o la lectura corregida en I‑MR).
    ``ranges``: el rango de cada subgrupo en X̄‑R; en I‑MR se ignora y se usan los rangos móviles.
    Devuelve ``{"center", "ucl", "lcl", "range_center", "range_ucl", "range_lcl"}``.
    """
    corrected_means = [to_decimal(value) for value in corrected_means]
    if chart_type == I_MR:
        if len(corrected_means) < 2:
            raise ValueError("An I-MR chart needs at least two readings in the reference period")
        ranges = [value for value in moving_ranges(corrected_means) if value is not None]
    else:
        if not corrected_means:
            raise ValueError("The reference period has no subgroups")
        ranges = [to_decimal(value) for value in ranges]
    center = mean(corrected_means)
    range_center = mean(ranges)
    a2, d3, d4 = (to_decimal(constants[key]) for key in ("a2", "d3", "d4"))
    return {
        "center": center,
        "ucl": center + a2 * range_center,
        "lcl": center - a2 * range_center,
        "range_center": range_center,
        "range_ucl": d4 * range_center,
        "range_lcl": d3 * range_center,
    }


def evaluate(corrected_mean, range_value, current_limits, nominal=None, tolerance=None):
    """``(fuera de control, fuera de aceptación, motivos)`` de un registro.

    Fuera de control: la media (o lectura) corregida fuera de LCI–LCS, o el rango (o
    rango móvil) fuera de sus límites. Fuera de aceptación: la media corregida se aleja
    del valor nominal más que la tolerancia del punto (criterio de aceptación).
    """
    reasons = []
    out_of_control = False
    if current_limits is not None:
        if not current_limits["lcl"] <= corrected_mean <= current_limits["ucl"]:
            out_of_control = True
            reasons.append("mean")
        if range_value is not None and not (
            current_limits["range_lcl"] <= range_value <= current_limits["range_ucl"]
        ):
            out_of_control = True
            reasons.append("range")
    out_of_acceptance = False
    if nominal is not None and tolerance is not None:
        if abs(corrected_mean - to_decimal(nominal)) > to_decimal(tolerance):
            out_of_acceptance = True
            reasons.append("acceptance")
    return out_of_control, out_of_acceptance, reasons


def rounded(value, places=6):
    if value is None:
        return None
    return to_decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
