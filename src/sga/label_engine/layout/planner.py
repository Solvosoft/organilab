# -*- coding: utf-8 -*-
"""
LabelPlanner: planificación declarativa del layout de una etiqueta.

El planner recibe un ``LabelBlueprint`` y las dimensiones del lienzo y produce un
``LayoutResult`` con una lista de ``Box`` ya resueltos (posición, tamaño, y un
``content_ref`` con fuentes/líneas/colores listos para pintar). No dibuja nada: toda
la medición se hace con ``Measurer`` sobre una superficie de scratch.

Los renderers (ver ``label_engine.renderers``) solo pintan estos boxes; toda la
decisión de acomodo vive aquí.

Fase 1: produce un layout limpio y declarativo respetando las zonas SGA probadas
(pictogramas arriba-izquierda, QR a la derecha, palabra de advertencia y frases).
La negociación de espacio multi-tamaño (reservar-luego-rellenar) llega en la Fase 2.
"""
from __future__ import annotations

import re
from datetime import datetime

from sga.label_engine import config
from sga.label_engine.models import LabelBlueprint, LabelTooSmallError
from sga.label_engine.resources import ResourceCache
from sga.label_engine.layout.box import Box, LayoutResult
from sga.label_engine.layout.measurer import Measurer
from sga.label_engine.phrases_catalog import expand_item, group_codes, normalize_code
from sga.label_engine.utils import normalize_text


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de frases H/P (portadas desde el engine)
# ─────────────────────────────────────────────────────────────────────────────
def _combine_codes(text: str) -> str:
    """Combina códigos H/P consecutivos: H314 H315 H316 → H314-H316."""
    if not text:
        return text
    codigos = re.findall(r"[HP]\d+[A-Z]*", text.upper())
    if not codigos:
        return text
    resultado = []
    i = 0
    while i < len(codigos):
        codigo = codigos[i]
        tipo = codigo[0]
        match = re.match(r"[HP](\d+)", codigo)
        if not match:
            resultado.append(codigo)
            i += 1
            continue
        num = int(match.group(1))
        j = i + 1
        inicio = num
        while j < len(codigos) and codigos[j][0] == tipo:
            m = re.match(r"[HP](\d+)", codigos[j])
            if m and int(m.group(1)) == num + (j - i):
                num = int(m.group(1))
                j += 1
            else:
                break
        if j > i + 1:
            resultado.append(f"{tipo}{inicio}-{codigos[j-1]}")
        else:
            resultado.append(codigo)
        i = j
    return " ".join(resultado)


# Un código H/P suelto o una combinación oficial. El ``+`` admite espacios
# alrededor porque así se registran en la base de datos ("P370 + P378").
_PHRASE_TOKEN = r"[HP]\d+[A-Za-z]*(?:\s*\+\s*[HP]\d+[A-Za-z]*)*"


def _split_phrase_items(text: str) -> list[str]:
    """Separa un bloque de frases en frases individuales.

    Una combinación ("P305 + P351 + P338") es una frase única, no tres.
    """
    if not text or not text.strip():
        return []
    text = text.replace("\r", "")
    parts = [p.strip(" ;,\t") for p in text.split("\n") if p.strip(" ;,\t")]
    if len(parts) > 1:
        return parts
    blob = parts[0] if parts else text.strip()
    if re.fullmatch(rf"(\s*{_PHRASE_TOKEN}\s*[,;]?\s*)+", blob):
        return [normalize_code(t) for t in re.findall(_PHRASE_TOKEN, blob)]
    return [blob]


def _phrase_codes_str(items: list[str]) -> str:
    """Compacta una lista de frases a sus códigos (P280 P305+P351+P338)."""
    codes = []
    for it in items:
        m = re.match(rf"\s*({_PHRASE_TOKEN})", it)
        if m:
            codes.append(normalize_code(m.group(1)))
    if not codes:
        return ""
    # Los rangos sólo se comprimen si todos son códigos sueltos: fusionar una
    # combinación con sus vecinos rompería la frase (P305+P351+P338 es una sola).
    if any("+" in c for c in codes):
        return " ".join(codes)
    return _combine_codes(" ".join(codes))


class LabelPlanner:
    """Planifica el layout de una etiqueta y emite boxes resueltos."""

    def __init__(self, resources: ResourceCache | None = None):
        self.resources = resources or ResourceCache()

    # ──────────────────────────────────────────────────────────────────────────
    def plan(self, bp: LabelBlueprint, ancho_px: int, alto_px: int) -> LayoutResult:
        # Piso absoluto: rechazar tamaños absurdos sin medir.
        min_w_mm, min_h_mm = config.MIN_LABEL_MM
        if bp.ancho_mm < min_w_mm or bp.alto_mm < min_h_mm:
            raise LabelTooSmallError(
                f"Etiqueta {bp.ancho_mm:g}×{bp.alto_mm:g} mm por debajo del mínimo "
                f"{min_w_mm:g}×{min_h_mm:g} mm."
            )

        m = Measurer(self.resources, dpi=bp.dpi)
        dim_ref = min(ancho_px, alto_px)
        margen = int(dim_ref * 0.02)
        margen_int = int(dim_ref * 0.01)

        boxes: list[Box] = []
        warnings: list[str] = []

        ctx = _Ctx(
            bp=bp,
            m=m,
            ancho=ancho_px,
            alto=alto_px,
            dim_ref=dim_ref,
            margen=margen,
            margen_int=margen_int,
            boxes=boxes,
            warnings=warnings,
        )

        # Si el nombre es corto, la palabra de advertencia va arriba-derecha (junto
        # al nombre) en vez de junto a los pictogramas. Se decide antes de negociar
        # para que la banda de pictogramas no reserve su altura.
        ctx.sig_topright = self._decide_signal_topright(ctx)

        # Negociación de espacio: elige la mayor escala del cuerpo que deja caber
        # el contenido obligatorio (incl. al menos una línea de frase H) entre el
        # header y el pie. Si ni a la escala mínima cabe → LabelTooSmallError.
        self._negotiate_scale(ctx)

        y = self._plan_header(ctx)
        name_top = y
        y = self._plan_name(ctx, y)
        y = self._plan_formula(ctx, y)
        if ctx.sig_topright:
            self._plan_signal_topright(ctx, name_top, y)
        y = self._plan_hazard(ctx, y)
        self._plan_phrases_and_footer(ctx, y)
        self._plan_border(ctx)

        return LayoutResult(boxes=boxes, total_height_used=alto_px, warnings=warnings)

    # ── Negociación de espacio (reservar-luego-rellenar) ───────────────────────
    def _negotiate_scale(self, ctx: "_Ctx") -> None:
        """Elige la mayor escala del cuerpo (≤1.0) que deja caber el contenido
        obligatorio entre el header y el pie, reservando al menos una línea de
        frase H a piso legible. Si ni a ``MIN_BODY_SCALE`` cabe → error."""
        m = ctx.m
        header_end = ctx.margen + self._header_height(ctx) + 2 * ctx.margen_int
        footer_top = self._footer_top(ctx)
        body_avail = footer_top - header_end

        # Reserva mínima obligatoria: las frases H como CÓDIGOS a piso legible
        # (el texto completo se mostrará si el espacio alcanza; si no, se degrada a
        # códigos en vez de fallar). Solo se falla si ni los códigos H caben.
        floor_font = m.font(
            self._min_phrase_font(m, ctx.bp.dpi, ctx.dim_ref), bold=False
        )
        lh = m.line_height(floor_font)
        inner = int(lh * 0.25)
        margin_cm_px = int(0.5 * ctx.bp.dpi / 25.4)
        x_min = ctx.margen + margin_cm_px
        _, x_qr, _ = self._qr_geom(ctx)
        x_max = min(ctx.ancho - ctx.margen - margin_cm_px, x_qr - ctx.margen_int)
        phr_w = max(int(ctx.dim_ref * 0.2), x_max - x_min)
        h_items = _split_phrase_items(ctx.bp.frases_peligro)
        h_codes = _phrase_codes_str(h_items)
        reserve_src = [h_codes] if h_codes else h_items
        h_lines = m.wrap_items(reserve_src, phr_w, floor_font) if reserve_src else []
        n_min = max(1, len(h_lines))
        min_phrase_h = n_min * (lh + inner)

        steps = [
            1.0 - 0.05 * i for i in range(int((1.0 - config.MIN_BODY_SCALE) / 0.05) + 1)
        ]
        for s in steps:
            if self._top_stack_height(ctx, s) + min_phrase_h <= body_avail:
                ctx.scale = s
                if s < 1.0:
                    ctx.warnings.append(f"cuerpo escalado a {s:.2f} para caber")
                return

        # Ni a la escala mínima cabe el contenido obligatorio.
        import math

        needed = (
            header_end
            + self._top_stack_height(ctx, config.MIN_BODY_SCALE)
            + min_phrase_h
            + (ctx.alto - footer_top)
        )
        alto_min_mm = math.ceil(needed * 25.4 / ctx.bp.dpi)
        raise LabelTooSmallError(
            f"Etiqueta {ctx.bp.ancho_mm:g}×{ctx.bp.alto_mm:g} mm insuficiente para el "
            f"contenido obligatorio (nombre, {n_min} línea(s) de frases H, pictogramas y "
            f"palabra de advertencia). Use al menos ~{alto_min_mm:g} mm de alto, "
            f"reduzca el contenido, o aumente el tamaño."
        )

    def _footer_top(self, ctx: "_Ctx") -> int:
        """Y donde termina el área de frases (inicio reservado del pie)."""
        m, bp = ctx.m, ctx.bp
        font_sb = m.font(int(ctx.dim_ref * 0.018), bold=True)
        rec = 0
        if bp.recipiente_nombre and bp.recipiente_color:
            rec = m.text_size(
                bp.recipiente_nombre, m.font(int(ctx.dim_ref * 0.016), bold=True)
            )[1] + int(ctx.alto * 0.018)
        y_pie1 = ctx.alto - int(ctx.alto * 0.09) - rec
        n_prep = (1 if bp.fabricante else 0) + (1 if bp.responsable else 0) + 1
        altura_prep = n_prep * int(m.text_size("A", font_sb)[1] * 1.2)
        return y_pie1 - altura_prep - ctx.margen_int

    def _top_stack_height(self, ctx: "_Ctx", scale: float) -> int:
        """Alto del cuerpo superior (nombre+fórmula+fila pictos+palabra) a una escala."""
        m, bp, dim = ctx.m, ctx.bp, ctx.dim_ref
        font_main = m.font(max(8, int(dim * 0.05 * scale)), bold=True)
        lineas = m.wrap(bp.nombre.upper(), int(ctx.ancho * 0.85), font_main)[:2]
        lh = int(m.line_height(font_main) * 1.2)
        h = len(lineas) * lh + ctx.margen_int // 2

        if bp.formula or bp.cas or bp.concentracion:
            fs_n = max(8, int(dim * 0.028 * scale))
            hm = m.text_size("A", m.font(fs_n))[1]
            h += (
                hm
                + (int(hm * 1.3) if bp.concentracion else 0)
                + int(ctx.margen_int * 0.8)
            )

        # Banda de pictogramas + palabra de advertencia (geometría compartida).
        band = self._hazard_metrics(ctx, scale)["band"]
        if band:
            h += band + ctx.margen_int
        return h

    # ── Header: logos + institucional + separador ─────────────────────────────
    def _plan_header(self, ctx: "_Ctx") -> int:
        bp, m = ctx.bp, ctx.m
        alto_logo = self._header_height(ctx)
        y_logo = ctx.margen

        # Logos: por organización si el blueprint los provee, si no los de defecto.
        logo_izq_key = bp.logo_izq_path or "una"
        logo_der_key = bp.logo_der_path or "quimica"

        w_una = 0
        logo_una = self.resources.get_logo(logo_izq_key)
        if logo_una:
            w_una = int(logo_una.width * (alto_logo / logo_una.height))
            ctx.boxes.append(
                Box(ctx.margen, y_logo, w_una, alto_logo, "logo", logo_izq_key)
            )

        x_der = ctx.ancho - ctx.margen
        w_quimica = 0
        logo_quimica = self.resources.get_logo(logo_der_key)
        if logo_quimica:
            w_quimica = int(logo_quimica.width * (alto_logo / logo_quimica.height))
            x_der -= w_quimica
            ctx.boxes.append(
                Box(x_der, y_logo, w_quimica, alto_logo, "logo", logo_der_key)
            )

        # Línea superior del encabezado: institución/organización (o el default).
        lines = [normalize_text(bp.institucion or "ESCUELA DE QUÍMICA")]
        if bp.catedra:
            lines.append(normalize_text(f"CÁTEDRA DE {bp.catedra}"))
        if bp.laboratorio:
            lines.append(normalize_text(f"Laboratorio {bp.laboratorio}"))

        font_size = int(ctx.dim_ref * 0.025)
        if logo_una and logo_quimica:
            espacio = x_der - (ctx.margen + w_una)
        else:
            espacio = ctx.ancho - 2 * ctx.margen
        font = m.font(font_size, bold=True)
        for linea in lines:
            if m.text_width(linea, font) > espacio:
                factor = espacio / max(1, m.text_width(linea, font)) * 0.95
                font_size = max(8, int(font_size * factor))
                font = m.font(font_size, bold=True)
                break

        alturas = [m.text_size(ln, font)[1] for ln in lines]
        alto_texto = sum(alturas) + (len(alturas) - 1) * (ctx.margen_int // 2)
        y_inst = y_logo + (alto_logo - alto_texto) // 2
        ctx.boxes.append(
            Box(
                0,
                y_inst,
                ctx.ancho,
                alto_texto,
                "text",
                {
                    "lines": lines,
                    "font_size": font_size,
                    "bold": True,
                    "color": config.INSTITUTIONAL_COLOR,
                    "align": "center",
                    "line_gap": ctx.margen_int // 2,
                },
            )
        )

        y = y_logo + alto_logo + ctx.margen_int
        ctx.boxes.append(
            Box(
                ctx.margen,
                y,
                ctx.ancho - 2 * ctx.margen,
                1,
                "rule",
                {"color": "#CCCCCC"},
            )
        )
        return y + ctx.margen_int

    # ── Nombre del reactivo + estado físico ───────────────────────────────────
    def _plan_name(self, ctx: "_Ctx", y: int) -> int:
        bp, m = ctx.bp, ctx.m
        fs_main = max(8, int(ctx.dim_ref * 0.05 * ctx.scale))
        fs_sub = max(8, int(ctx.dim_ref * 0.03 * ctx.scale))
        font_main = m.font(fs_main, bold=True)

        nombre = bp.nombre.upper()
        max_ancho = int(ctx.ancho * 0.85)
        lineas = m.wrap(nombre, max_ancho, font_main)
        truncated = len(lineas) > 2
        lineas = lineas[:2]

        suffix = ""
        if bp.estado_fisico == "l":
            suffix = normalize_text("(líq)")
        elif bp.estado_fisico:
            suffix = normalize_text(f"({bp.estado_fisico})")

        lh = int(m.line_height(font_main) * 1.2)
        alto = len(lineas) * lh + (lh if truncated else 0)
        ctx.boxes.append(
            Box(
                ctx.margen,
                y,
                max_ancho,
                alto,
                "name",
                {
                    "lines": lineas,
                    "suffix": suffix,
                    "truncated": truncated,
                    "font_size_main": fs_main,
                    "font_size_sub": fs_sub,
                    "line_gap": lh,
                },
            )
        )
        y += len(lineas) * lh + (lh if truncated else 0)
        return y + ctx.margen_int // 2

    # ── Fórmula + CAS + concentración ─────────────────────────────────────────
    def _plan_formula(self, ctx: "_Ctx", y: int) -> int:
        bp, m = ctx.bp, ctx.m
        fs_n = max(8, int(ctx.dim_ref * 0.028 * ctx.scale))
        fs_s = max(8, int(ctx.dim_ref * 0.018 * ctx.scale))
        font_n = m.font(fs_n, bold=False)
        h_main = m.text_size("A", font_n)[1]

        # El estado físico ya se pinta junto al nombre (_plan_name); repetirlo
        # aquí lo solapaba con la fórmula en tamaños pequeños.
        if not (bp.formula or bp.cas or bp.concentracion):
            return y

        ctx.boxes.append(
            Box(
                ctx.margen,
                y,
                ctx.ancho - 2 * ctx.margen,
                int(h_main * 2.5),
                "formula",
                {
                    "formula": bp.formula,
                    "cas": bp.cas,
                    "concentracion": bp.concentracion,
                    "estado_suffix": "",
                    "font_size_main": fs_n,
                    "font_size_sub": fs_s,
                    "font_size_sup": fs_s,
                    "line_gap": int(h_main * 1.3),
                },
            )
        )

        consumed = h_main
        if bp.concentracion:
            consumed += int(h_main * 1.3)
        return y + consumed + int(ctx.margen_int * 0.8)

    # ── Dimensiones de banda (header / pictogramas) ───────────────────────────
    @staticmethod
    def _header_height(ctx: "_Ctx") -> int:
        """Alto de la banda de cabecera (logos). Más generoso que antes para que
        los logos y el texto institucional se vean bien, sobre todo en grandes."""
        return max(int(ctx.alto * 0.09), int(ctx.dim_ref * 0.06))

    @staticmethod
    def _fit_font_width(
        m: Measurer,
        text: str,
        max_w: int,
        max_fs: int,
        bold: bool = True,
        min_fs: int = 8,
    ) -> int:
        """Mayor tamaño de fuente (≤max_fs) cuyo ancho de ``text`` cabe en max_w."""
        fs = max(min_fs, max_fs)
        while fs > min_fs and m.text_width(text, m.font(fs, bold=bold)) > max_w:
            fs -= 1
        return fs

    @staticmethod
    def _picto_size(ctx: "_Ctx", n: int) -> int:
        """Lado del pictograma: prominente (≈17% del alto), acotado por el ancho
        disponible a la izquierda del QR para que la fila no se monte sobre él."""
        base = max(24, int(ctx.alto * 0.17))
        _, x_qr, _ = LabelPlanner._qr_geom(ctx)
        gap = int(ctx.margen_int * 0.5)
        avail_w = (x_qr - ctx.margen - ctx.margen_int) - max(0, n - 1) * gap
        if n > 0:
            base = min(base, max(20, avail_w // n))
        return max(20, base)

    @staticmethod
    def _estado_suffix(bp) -> str:
        if bp.estado_fisico == "l":
            return normalize_text("(líq)")
        if bp.estado_fisico:
            return normalize_text(f"({bp.estado_fisico})")
        return ""

    def _name_width(self, ctx: "_Ctx", scale: float) -> int:
        """Ancho (px) que ocupa el nombre (línea más ancha + sufijo de estado)."""
        m, bp = ctx.m, ctx.bp
        font_main = m.font(max(8, int(ctx.dim_ref * 0.05 * scale)), bold=True)
        lineas = m.wrap(bp.nombre.upper(), int(ctx.ancho * 0.85), font_main)[:2]
        if not lineas:
            return 0
        w = max(m.text_width(ln, font_main) for ln in lineas)
        suffix = self._estado_suffix(bp)
        if suffix:
            font_sub = m.font(max(8, int(ctx.dim_ref * 0.03 * scale)), bold=True)
            w = max(
                w,
                m.text_width(lineas[-1], font_main)
                + m.text_width(suffix, font_sub)
                + 4,
            )
        return w

    def _decide_signal_topright(self, ctx: "_Ctx") -> bool:
        """¿Cabe la palabra de advertencia arriba-derecha (junto al nombre)?
        Solo si el nombre es lo bastante corto para dejar un bloque útil a su
        derecha (decisión con escala 1.0, estable antes de negociar)."""
        bp, m = ctx.bp, ctx.m
        if not bp.palabra_advertencia:
            return False
        name_w = self._name_width(ctx, 1.0)
        x0 = ctx.margen + name_w + 2 * ctx.margen_int
        avail = (ctx.ancho - ctx.margen) - x0
        comf = max(8, int(ctx.dim_ref * config.WARNING_FONT_RATIO))
        fits = m.text_width(bp.palabra_advertencia, m.font(comf, bold=True)) <= avail
        return avail >= int(ctx.ancho * 0.28) and fits

    def _plan_signal_topright(self, ctx: "_Ctx", y0: int, y1: int) -> None:
        """Coloca la palabra de advertencia en la esquina superior derecha,
        alineada a la derecha y centrada verticalmente en la banda nombre+fórmula,
        creciendo para llenar el espacio libre a la derecha del nombre."""
        bp, m = ctx.bp, ctx.m
        palabra = bp.palabra_advertencia
        name_w = self._name_width(ctx, ctx.scale)
        x0 = ctx.margen + name_w + 2 * ctx.margen_int
        region_w = (ctx.ancho - ctx.margen) - x0
        region_h = max(1, y1 - y0)
        max_fs = max(8, int(min(ctx.dim_ref * 0.18, region_h)))
        fs = self._fit_font_width(m, palabra, region_w, max_fs)
        fw, fh = m.text_size(palabra, m.font(fs, bold=True))
        x = (ctx.ancho - ctx.margen) - fw
        yy = y0 + max(0, (region_h - fh) // 2)
        color = (
            config.BORDER_COLORS["PELIGRO"]
            if palabra.upper() == "PELIGRO"
            else config.BORDER_COLORS.get("ATENCION", "#FFA500")
        )
        ctx.boxes.append(
            Box(
                x,
                yy,
                fw,
                fh,
                "text",
                {
                    "lines": [palabra],
                    "font_size": fs,
                    "bold": True,
                    "color": color,
                    "align": "left",
                    "line_gap": 0,
                },
            )
        )

    def _hazard_metrics(self, ctx: "_Ctx", scale: float) -> dict:
        """Geometría de la banda de peligro (pictogramas + palabra de advertencia).

        La palabra se coloca a tamaño pleno (≈``WARNING_FONT_RATIO``):
        - AL LADO de los pictogramas si cabe a ese tamaño;
        - si no, en su PROPIA LÍNEA debajo (a ancho completo, encogiendo solo si
          fuera estrictamente necesario para no invadir el QR).
        Devuelve todo lo necesario para colocar y para estimar el alto de la banda.
        """
        m, bp = ctx.m, ctx.bp
        osha = [s for s in bp.simbolos if s in config.PICTOGRAMAS_OSHA][
            : config.MAX_OSHA_PICTOGRAMS
        ]
        n = len(osha)
        tam_picto = self._picto_size(ctx, n) if n else 0
        gap = int(ctx.margen_int * 0.5)
        row_w = n * tam_picto + max(0, n - 1) * gap
        row_h = tam_picto if n else 0
        x_pictos_end = ctx.margen + row_w
        _, x_qr, _ = self._qr_geom(ctx)

        d = {
            "osha": osha,
            "tam_picto": tam_picto,
            "row_h": row_h,
            "x_pictos_end": x_pictos_end,
            "x_qr": x_qr,
            "palabra": bp.palabra_advertencia,
            "sig_below": False,
            "sig_fs": 0,
            "sig_sh": 0,
            "sig_x": ctx.margen,
            "sig_w": 0,
        }
        palabra = bp.palabra_advertencia
        if palabra and not ctx.sig_topright:
            # La palabra de advertencia CRECE para llenar el espacio disponible
            # (prominente, como exige el SGA), no a un tamaño fijo modesto.
            min_prominente = max(8, int(ctx.dim_ref * 0.05))
            x_beside = (x_pictos_end + ctx.margen_int) if row_h else ctx.margen
            avail_beside = x_qr - ctx.margen_int - x_beside
            # Tope de tamaño al lado: acotado por ancho y por una altura razonable.
            max_fs_beside = max(8, int(min(ctx.dim_ref * 0.16, ctx.alto * 0.20)))
            fs_beside = self._fit_font_width(m, palabra, avail_beside, max_fs_beside)
            if row_h and fs_beside >= min_prominente:
                d.update(
                    sig_below=False,
                    sig_fs=fs_beside,
                    sig_sh=m.text_size(palabra, m.font(fs_beside, bold=True))[1],
                    sig_x=x_beside,
                    sig_w=avail_beside,
                )
            else:
                # Propia línea debajo, a ancho completo (también crece).
                avail_below = max(
                    int(ctx.dim_ref * 0.1), x_qr - ctx.margen_int - ctx.margen
                )
                max_fs_below = max(8, int(min(ctx.dim_ref * 0.11, ctx.alto * 0.14)))
                fs_below = self._fit_font_width(m, palabra, avail_below, max_fs_below)
                d.update(
                    sig_below=True,
                    sig_fs=fs_below,
                    sig_sh=m.text_size(palabra, m.font(fs_below, bold=True))[1],
                    sig_x=ctx.margen,
                    sig_w=avail_below,
                )

        if d["sig_below"]:
            band = row_h + (ctx.margen_int if row_h else 0) + d["sig_sh"]
        else:
            band = max(row_h, d["sig_sh"])
        d["band"] = band
        return d

    # ── Geometría del QR (centralizada) ───────────────────────────────────────
    @staticmethod
    def _qr_geom(ctx: "_Ctx") -> tuple[int, int, int]:
        """Tamaño y posición del QR: centrado en la banda vertical y=40-80%,
        pegado al margen derecho. Más grande que antes para que sea claramente
        escaneable y ocupe su zona (mejora legibilidad y detección).
        Devuelve (tam_qr, x_qr, y_qr)."""
        tam_qr = max(1, min(int(ctx.alto * 0.40), int(ctx.ancho * 0.30)))
        x_qr = ctx.ancho - ctx.margen - tam_qr
        y_qr = int(ctx.alto * 0.60) - tam_qr // 2
        return tam_qr, x_qr, y_qr

    # ── Pictogramas + QR + EPP ────────────────────────────────────────────────
    def _plan_hazard(self, ctx: "_Ctx", y: int) -> int:
        bp = ctx.bp
        tam_qr, x_qr, y_qr = self._qr_geom(ctx)
        epp = [s for s in bp.simbolos if s in config.PICTOGRAMAS_EPP]

        d = self._hazard_metrics(ctx, ctx.scale)
        tam_picto, row_h = d["tam_picto"], d["row_h"]

        # Fila de pictogramas OSHA, centrada verticalmente en la banda (cuya altura
        # puede venir dada por la palabra de advertencia).
        x_picto = ctx.margen
        picto_y = y + max(0, (d["band"] - row_h) // 2)
        for simb in d["osha"]:
            ctx.boxes.append(
                Box(
                    x_picto,
                    picto_y,
                    tam_picto,
                    tam_picto,
                    "pictogram",
                    {"symbol": simb},
                )
            )
            x_picto += tam_picto + int(ctx.margen_int * 0.5)

        # Palabra de advertencia a tamaño pleno: al lado de los pictogramas si cabe,
        # o en su propia línea debajo. (Si va arriba-derecha, no se coloca aquí.)
        palabra = d["palabra"]
        if palabra and not ctx.sig_topright:
            color = (
                config.BORDER_COLORS["PELIGRO"]
                if palabra.upper() == "PELIGRO"
                else config.BORDER_COLORS.get("ATENCION", "#FFA500")
            )
            if d["sig_below"]:
                sig_y = y + (row_h + ctx.margen_int if row_h else 0)
            else:
                sig_y = y + (d["band"] - d["sig_sh"]) // 2
            ctx.boxes.append(
                Box(
                    d["sig_x"],
                    sig_y,
                    d["sig_w"],
                    d["sig_sh"],
                    "text",
                    {
                        "lines": [palabra],
                        "font_size": d["sig_fs"],
                        "bold": True,
                        "color": color,
                        "align": "left",
                        "line_gap": 0,
                    },
                )
            )

        # QR en el rail derecho, en su banda fija (flota junto a las frases).
        # La URL la inyecta el blueprint (por organización/sustancia); "" = default.
        ctx.boxes.append(Box(x_qr, y_qr, tam_qr, tam_qr, "qr", {"url": bp.qr_url}))

        # Pictogramas EPP debajo del QR, sin invadir el pie.
        if epp:
            spacing = int(ctx.margen_int * 0.35)
            epp_top = y_qr + tam_qr + spacing
            epp_limit = ctx.alto - int(ctx.alto * 0.12)
            avail = max(0, epp_limit - epp_top)
            if avail > 0:
                tam_epp = min(
                    tam_picto,
                    max(int((avail - spacing * (len(epp) - 1)) / len(epp)), 16),
                )
            else:
                tam_epp = 16
            x_center = x_qr + (tam_qr - tam_epp) // 2
            y_epp = epp_top
            for simb in epp:
                ctx.boxes.append(
                    Box(
                        x_center, y_epp, tam_epp, tam_epp, "pictogram", {"symbol": simb}
                    )
                )
                y_epp += tam_epp + spacing

        # La columna izquierda continúa justo bajo la banda de pictogramas + palabra.
        return y + (d["band"] + ctx.margen_int if d["band"] else 0)

    # ── Frases H/P + info + pie ────────────────────────────────────────────────
    def _plan_phrases_and_footer(self, ctx: "_Ctx", y: int) -> None:
        bp, m = ctx.bp, ctx.m
        fs_small = int(ctx.dim_ref * 0.018)
        fs_recipiente = int(ctx.dim_ref * 0.016)
        font_small_bold = m.font(fs_small, bold=True)
        font_recipiente = m.font(fs_recipiente, bold=True)
        altura_linea = m.line_height(font_small_bold)

        recipiente_nombre = bp.recipiente_nombre
        recipiente_color = bp.recipiente_color
        alto_texto_rec = 0
        if recipiente_nombre and recipiente_color:
            alto_texto_rec = m.text_size(recipiente_nombre, font_recipiente)[1] + int(
                ctx.alto * 0.018
            )

        y_pie1 = ctx.alto - int(ctx.alto * 0.09) - alto_texto_rec

        # Preparador / fecha / fabricante
        fecha_prep = bp.fecha_preparacion or datetime.now().strftime("%d/%m/%Y")
        textos_prep = []
        if bp.fabricante:
            textos_prep.append(f"Fabricante: {bp.fabricante}")
        if bp.responsable:
            textos_prep.append(f"Preparador: {bp.responsable}")
        textos_prep.append(f"Fecha de Preparación: {fecha_prep}")
        altura_prep = len(textos_prep) * int(m.text_size("A", font_small_bold)[1] * 1.2)

        y_frases_start = y + ctx.margen_int
        y_frases_end = y_pie1 - altura_prep - ctx.margen_int

        if y_frases_end - y_frases_start > int(ctx.alto * 0.1):
            margin_cm_px = int(0.5 * bp.dpi / 25.4)
            x_min = ctx.margen + margin_cm_px
            _, x_qr, _ = self._qr_geom(ctx)
            x_max = min(ctx.ancho - ctx.margen - margin_cm_px, x_qr - ctx.margen_int)
            max_width = max(int(ctx.dim_ref * 0.2), x_max - x_min)
            avail_h = y_frases_end - y_frases_start

            h_items = _split_phrase_items(bp.frases_peligro)
            p_items = _split_phrase_items(bp.consejos_prudencia)
            y_actual = y_frases_start
            if h_items or p_items:
                plan = self._fit_phrase_block(
                    m, h_items, p_items, max_width, avail_h, ctx.dim_ref, bp.dpi
                )
                ctx.boxes.append(
                    Box(
                        x_min,
                        y_frases_start,
                        max_width,
                        avail_h,
                        "phrases",
                        plan,
                    )
                )
                y_actual = y_frases_start + self._phrase_block_height(plan)

            if bp.info_adicional and y_actual < y_frases_end:
                fs_info = self._min_phrase_font(m, bp.dpi, ctx.dim_ref)
                font_info = m.font(fs_info, bold=False)
                lines_i = m.wrap_items([bp.info_adicional], max_width, font_info)
                alt_i = m.text_size("Ag", font_info)[1]
                fit_lines = []
                yy = y_actual
                for linea in lines_i:
                    if yy + alt_i > y_frases_end:
                        break
                    fit_lines.append(linea)
                    yy += alt_i + int(ctx.margen_int * 0.2)
                if fit_lines:
                    ctx.boxes.append(
                        Box(
                            x_min,
                            y_actual,
                            max_width,
                            yy - y_actual,
                            "text",
                            {
                                "lines": fit_lines,
                                "font_size": fs_info,
                                "bold": False,
                                "color": config.INFO_COLOR,
                                "align": "center",
                                "line_gap": int(ctx.margen_int * 0.2),
                            },
                        )
                    )

        # Pie: lote / caducidad / cantidad
        textos_pie = []
        if bp.lote:
            textos_pie.append(f"Lote: {bp.lote}")
        if bp.fecha_caducidad:
            textos_pie.append(f"Caducidad: {bp.fecha_caducidad}")
        if bp.cantidad:
            textos_pie.append(f"Cantidad: {bp.cantidad}")
        if bp.ubicacion:
            textos_pie.append(f"Ubicación: {bp.ubicacion}")

        if textos_pie:
            ancho_disp = ctx.ancho - 2 * ctx.margen
            pie_lines: list[str] = []
            cur: list[str] = []
            for t in textos_pie:
                test = "  •  ".join(cur + [t])
                if cur and m.text_width(test, font_small_bold) > ancho_disp:
                    pie_lines.append("  •  ".join(cur))
                    cur = [t]
                else:
                    cur.append(t)
            if cur:
                pie_lines.append("  •  ".join(cur))
            ctx.boxes.append(
                Box(
                    ctx.margen,
                    y_pie1,
                    ctx.ancho - 2 * ctx.margen,
                    altura_linea * len(pie_lines),
                    "text",
                    {
                        "lines": pie_lines,
                        "font_size": fs_small,
                        "bold": True,
                        "color": config.MISC_COLOR,
                        "align": "left",
                        "line_gap": int(altura_linea * 0.2),
                    },
                )
            )

        # Preparador
        y_prep = y_pie1 - altura_prep - ctx.margen_int
        ctx.boxes.append(
            Box(
                ctx.margen,
                y_prep,
                ctx.ancho - 2 * ctx.margen,
                altura_prep,
                "text",
                {
                    "lines": textos_prep,
                    "font_size": fs_small,
                    "bold": True,
                    "color": config.MISC_COLOR,
                    "align": "left",
                    "line_gap": int(m.text_size("A", font_small_bold)[1] * 0.2),
                },
            )
        )

        # Recipiente
        if recipiente_nombre and recipiente_color:
            th = m.text_size(recipiente_nombre, font_recipiente)[1]
            thickness = max(3, int(min(ctx.ancho, ctx.alto) * 0.008))
            y_rec = ctx.alto - thickness - th - int(ctx.alto * 0.01)
            ctx.boxes.append(
                Box(
                    0,
                    y_rec,
                    ctx.ancho,
                    th,
                    "text",
                    {
                        "lines": [recipiente_nombre],
                        "font_size": fs_recipiente,
                        "bold": True,
                        "color": recipiente_color,
                        "align": "center",
                        "line_gap": 0,
                    },
                )
            )

    # ── Marco ──────────────────────────────────────────────────────────────────
    def _plan_border(self, ctx: "_Ctx") -> None:
        palabra = ctx.bp.palabra_advertencia.upper()
        if "PELIGRO" in palabra or "ATENCI" in palabra:
            thickness = max(4, int(ctx.dim_ref * 0.01))
        else:
            thickness = max(3, int(ctx.dim_ref * 0.008))
        ctx.boxes.append(
            Box(
                0,
                0,
                ctx.ancho,
                ctx.alto,
                "border",
                {
                    "palabra_advertencia": ctx.bp.palabra_advertencia,
                    "thickness": thickness,
                },
                z_index=10,
            )
        )

        # Acento del color del recipiente: marco interno justo por dentro del
        # marco reglamentario (que conserva su color SGA). z<border para no taparlo.
        if ctx.bp.recipiente_color:
            acc_thickness = max(2, int(ctx.dim_ref * 0.006))
            ctx.boxes.append(
                Box(
                    0,
                    0,
                    ctx.ancho,
                    ctx.alto,
                    "accent",
                    {
                        "color": ctx.bp.recipiente_color,
                        "thickness": acc_thickness,
                        "inset": thickness,
                    },
                    z_index=9,
                )
            )

    # ── Cascada de degradación de frases (portada del engine) ──────────────────
    @staticmethod
    def _min_phrase_font(m: Measurer, dpi: int, dim_ref: int) -> int:
        floor = m.mm_to_px(config.MIN_PHRASE_FONT_MM)
        return max(8, min(floor, max(8, int(dim_ref * 0.04))))

    def _fit_phrase_block(
        self, m: Measurer, h_items, p_items, max_width, avail_h, dim_ref, dpi
    ) -> dict:
        """Decide tamaño y contenido de las frases.

        Prioriza el TEXTO COMPLETO de las indicaciones (SGA), eligiendo la mayor
        fuente que quepa (crecer hasta llenar). Si el texto no cabe ni al piso
        legible, degrada en orden: recortar P → P como códigos → quitar P →
        H como CÓDIGOS (último recurso) → truncar. Siempre añade la referencia a
        la FDS cuando algo se omite.
        """
        min_font = self._min_phrase_font(m, dpi, dim_ref)
        comfortable = max(min_font, int(dim_ref * 0.05))  # tope al crecer
        fds = config.FDS_REFERENCE_TEXT

        # Agrupar en combinaciones SGA oficiales (P305+P351+P338, etc.) y obtener
        # las formas: texto completo (combinado) y solo códigos (también combinados).
        h_groups = group_codes(h_items, "H")
        p_groups = group_codes(p_items, "P")
        h_full = [full for _, full in h_groups]
        p_full = [full for _, full in p_groups]
        h_codes = " ".join(cs for cs, _ in h_groups if cs) or _phrase_codes_str(h_items)
        p_codes = " ".join(cs for cs, _ in p_groups if cs) or _phrase_codes_str(p_items)

        def stacked(*groups, spacing, gap):
            # Debe coincidir EXACTAMENTE con _phrase_block_height / el renderer:
            # cada línea avanza (lh + inner), incluida la última de cada grupo, y
            # hay un 'gap' entre grupos. Si se subestima, la última línea invade el pie.
            gs = [g for g in groups if g]
            if not gs:
                return 0
            inner = int(spacing * 0.25)
            total = sum(len(g) * (spacing + inner) for g in gs)
            return total + (len(gs) - 1) * gap

        def metrics(fs):
            font = m.font(fs, bold=False)
            lh = m.line_height(font)
            return font, lh, max(2, int(lh * 0.4))

        # Fase 1: TEXTO COMPLETO de H y P; mayor fuente que quepa (llenar).
        for fs in range(comfortable, min_font - 1, -1):
            font, lh, gap = metrics(fs)
            h_lines = m.wrap_items(h_full, max_width, font)
            p_lines = m.wrap_items(p_full, max_width, font)
            if stacked(h_lines, p_lines, spacing=lh, gap=gap) <= avail_h:
                return self._make_plan(fs, lh, gap, h_lines, p_lines, None)

        # A partir de aquí, al piso legible.
        font, lh, gap = metrics(min_font)
        fds_lines = m.wrap_items([fds], max_width, font)
        h_full_lines = m.wrap_items(h_full, max_width, font)

        # Fase 2: H completo + TODOS los P como códigos (preserva todos los
        # consejos; "código solo si el texto no cabe") + FDS.
        if p_codes:
            p_lines = m.wrap_items([p_codes], max_width, font)
            if (
                stacked(h_full_lines, p_lines, fds_lines, spacing=lh, gap=gap)
                <= avail_h
            ):
                return self._make_plan(
                    min_font, lh, gap, h_full_lines, p_lines, fds_lines
                )

        # Fase 3: H completo + FDS (sin P; la FDS cubre la prudencia).
        if stacked(h_full_lines, fds_lines, spacing=lh, gap=gap) <= avail_h:
            return self._make_plan(
                min_font, lh, gap, h_full_lines, [], fds_lines if p_items else None
            )

        # Fase 4: H como CÓDIGOS (solo porque el texto no cabe) + P códigos + FDS.
        h_code_lines = m.wrap_items([h_codes] if h_codes else h_full, max_width, font)
        if p_codes:
            p_lines = m.wrap_items([p_codes], max_width, font)
            if (
                stacked(h_code_lines, p_lines, fds_lines, spacing=lh, gap=gap)
                <= avail_h
            ):
                return self._make_plan(
                    min_font, lh, gap, h_code_lines, p_lines, fds_lines
                )

        # Fase 5: H códigos + FDS.
        if stacked(h_code_lines, fds_lines, spacing=lh, gap=gap) <= avail_h:
            return self._make_plan(min_font, lh, gap, h_code_lines, [], fds_lines)

        # Fase 6: truncar H códigos + FDS (último recurso).
        fds_h = stacked(fds_lines, spacing=lh, gap=gap)
        usable = max(0, avail_h - fds_h - gap)
        per_line = lh + int(lh * 0.25)
        max_lines = max(1, usable // per_line) if per_line else 1
        return self._make_plan(
            min_font, lh, gap, h_code_lines[:max_lines], [], fds_lines
        )

    @staticmethod
    def _make_plan(font_size, lh, gap, h_lines, p_lines, fds_lines) -> dict:
        return {
            "font_size": font_size,
            "line_height": lh,
            "gap": gap,
            "inner": int(lh * 0.25),
            "h_lines": h_lines,
            "p_lines": p_lines,
            "fds_lines": fds_lines or [],
        }

    @staticmethod
    def _phrase_block_height(plan: dict) -> int:
        lh, inner, gap = plan["line_height"], plan["inner"], plan["gap"]
        y = 0
        if plan["h_lines"]:
            y += len(plan["h_lines"]) * (lh + inner)
        if plan["p_lines"]:
            y += gap + len(plan["p_lines"]) * (lh + inner)
        if plan["fds_lines"]:
            y += gap + len(plan["fds_lines"]) * (lh + inner)
        return y


class _Ctx:
    """Estado compartido durante la planificación de una etiqueta."""

    __slots__ = (
        "bp",
        "m",
        "ancho",
        "alto",
        "dim_ref",
        "margen",
        "margen_int",
        "boxes",
        "warnings",
        "scale",
        "sig_topright",
    )

    def __init__(
        self, bp, m, ancho, alto, dim_ref, margen, margen_int, boxes, warnings
    ):
        self.bp = bp
        self.m = m
        self.ancho = ancho
        self.alto = alto
        self.dim_ref = dim_ref
        self.margen = margen
        self.margen_int = margen_int
        self.boxes = boxes
        self.warnings = warnings
        self.scale = 1.0  # factor de escala del cuerpo (negociación de espacio)
        self.sig_topright = False  # palabra de advertencia en esquina superior derecha
