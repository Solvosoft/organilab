# -*- coding: utf-8 -*-
"""
Generador de etiquetas GHS/SGA para reactivos químicos.
Módulo standalone sin dependencias de tkinter.

Basado en el proyecto Etiquetador - Escuela de Química, UNA.
Cumple RTCR 481:2015 (SGA/GHS).
"""

import io
import os
import re
import logging
import platform
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import qrcode

logger = logging.getLogger(__name__)

# Pictogramas GHS → nombres de archivo EPS
PICTOGRAMAS_OSHA = {
    "Explosivo": "exploding_bomb.eps",
    "Inflamable": "flame.eps",
    "Comburente": "flame_over_circle.eps",
    "Gas Comprimido": "gas_cylinder.eps",
    "Corrosivo": "corrosion.eps",
    "Tóxico": "skull_crossbones.eps",
    "Peligro para la Salud": "health_hazard.eps",
    "Peligro Ambiental": "environment.eps",
    "Irritante": "exclamation.eps",
}

# H-code → pictograma(s) según estándar GHS
HCODE_PICTOGRAMAS = {
    'H200': ['Explosivo'], 'H201': ['Explosivo'], 'H202': ['Explosivo'],
    'H203': ['Explosivo'], 'H204': ['Explosivo'], 'H205': ['Explosivo'],
    'H220': ['Inflamable'], 'H221': ['Inflamable'], 'H222': ['Inflamable'],
    'H223': ['Inflamable'], 'H224': ['Inflamable'], 'H225': ['Inflamable'],
    'H226': ['Inflamable'], 'H227': ['Inflamable'], 'H228': ['Inflamable'],
    'H229': ['Gas Comprimido'],
    'H240': ['Explosivo'], 'H241': ['Explosivo'], 'H242': ['Inflamable'],
    'H250': ['Inflamable'], 'H251': ['Inflamable'], 'H252': ['Inflamable'],
    'H260': ['Inflamable'], 'H261': ['Inflamable'],
    'H270': ['Comburente'], 'H271': ['Comburente'], 'H272': ['Comburente'],
    'H280': ['Gas Comprimido'], 'H281': ['Gas Comprimido'],
    'H290': ['Corrosivo'],
    'H300': ['Tóxico'], 'H301': ['Tóxico'], 'H302': ['Irritante'],
    'H304': ['Peligro para la Salud'], 'H305': ['Peligro para la Salud'],
    'H310': ['Tóxico'], 'H311': ['Tóxico'], 'H312': ['Irritante'],
    'H314': ['Corrosivo'], 'H315': ['Irritante'], 'H317': ['Irritante'],
    'H318': ['Corrosivo'], 'H319': ['Irritante'],
    'H330': ['Tóxico'], 'H331': ['Tóxico'], 'H332': ['Irritante'],
    'H334': ['Peligro para la Salud'], 'H335': ['Irritante'], 'H336': ['Irritante'],
    'H340': ['Peligro para la Salud'], 'H341': ['Peligro para la Salud'],
    'H350': ['Peligro para la Salud'], 'H351': ['Peligro para la Salud'],
    'H360': ['Peligro para la Salud'], 'H361': ['Peligro para la Salud'],
    'H362': ['Peligro para la Salud'],
    'H370': ['Peligro para la Salud'], 'H371': ['Peligro para la Salud'],
    'H372': ['Peligro para la Salud'], 'H373': ['Peligro para la Salud'],
    'H400': ['Peligro Ambiental'], 'H410': ['Peligro Ambiental'],
    'H411': ['Peligro Ambiental'], 'H412': ['Peligro Ambiental'],
    'H413': ['Peligro Ambiental'], 'H420': ['Peligro Ambiental'],
}


# ------------------------------------------------------------------
# Fuentes
# ------------------------------------------------------------------
_FUENTE_CACHE = {}
_FUENTE_RUTA_CACHE = {}


def _candidatos_fuente(bold):
    candidatos = []
    sistema = platform.system()
    if sistema == "Windows":
        candidatos += [
            r"C:\Windows\Fonts\DejaVuSans-Bold.ttf" if bold else r"C:\Windows\Fonts\DejaVuSans.ttf",
            r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        ]
    elif sistema == "Darwin":
        candidatos += [
            "/Library/Fonts/DejaVuSans-Bold.ttf" if bold else "/Library/Fonts/DejaVuSans.ttf",
        ]
    else:
        candidatos += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]
    return candidatos


def obtener_fuente(tamano, bold=False):
    tamano = max(1, int(tamano))
    clave = (bold, tamano)
    if clave in _FUENTE_CACHE:
        return _FUENTE_CACHE[clave]

    if bold not in _FUENTE_RUTA_CACHE:
        encontrada = None
        for ruta in _candidatos_fuente(bold):
            if os.path.exists(ruta):
                encontrada = ruta
                break
        _FUENTE_RUTA_CACHE[bold] = encontrada

    ruta = _FUENTE_RUTA_CACHE[bold]
    if ruta is None:
        fuente = ImageFont.load_default()
    else:
        try:
            fuente = ImageFont.truetype(ruta, tamano)
        except Exception:
            fuente = ImageFont.load_default()

    _FUENTE_CACHE[clave] = fuente
    return fuente


# ------------------------------------------------------------------
# Resolución de pictogramas desde H-codes
# ------------------------------------------------------------------
def resolver_pictogramas(h_codes):
    """Retorna lista de nombres de pictogramas a partir de H-codes."""
    pictogramas = set()
    for code in h_codes:
        partes = [p.strip() for p in code.replace(" + ", "+").split("+")]
        for parte in partes:
            if parte in HCODE_PICTOGRAMAS:
                pictogramas.update(HCODE_PICTOGRAMAS[parte])
    return sorted(pictogramas)


def resolver_palabra_advertencia(warning_words_qs):
    """Determina la palabra de advertencia más severa de un queryset de WarningWord."""
    palabra = ""
    for ww in warning_words_qs:
        nombre = (ww.name or "").strip().lower()
        if nombre == "peligro":
            return "PELIGRO"
        elif nombre in ("atención", "atencion"):
            palabra = "ATENCIÓN"
    return palabra


# ------------------------------------------------------------------
# Clase principal
# ------------------------------------------------------------------
class LabelGenerator:
    """Genera etiquetas GHS/SGA como imágenes PIL."""

    def __init__(self, logo_izq_path=None, logo_der_path=None,
                 pictogramas_dir=None):
        """
        Args:
            logo_izq_path: Ruta al logo izquierdo (opcional).
            logo_der_path: Ruta al logo derecho (opcional).
            pictogramas_dir: Carpeta con archivos EPS de pictogramas OSHA.
        """
        self.logo_izq = self._cargar_logo(logo_izq_path)
        self.logo_der = self._cargar_logo(logo_der_path)
        self.pictogramas_dir = pictogramas_dir
        self.cache_pictogramas = {}

    @staticmethod
    def _cargar_logo(path):
        if path and os.path.exists(path):
            try:
                return Image.open(path).convert('RGBA')
            except Exception as e:
                logger.warning(f"No se pudo cargar logo {path}: {e}")
        return None

    # --- Helpers para fórmulas con subíndices ---
    @staticmethod
    def _parsear_formula(formula):
        tokens = []
        i = 0
        s = formula
        while i < len(s):
            if s[i] in ('_', '^'):
                kind = 's' if s[i] == '_' else 'p'
                i += 1
                if i < len(s) and s[i] == '{':
                    j = s.find('}', i + 1)
                    if j == -1:
                        contenido = s[i + 1:]
                        i = len(s)
                    else:
                        contenido = s[i + 1:j]
                        i = j + 1
                else:
                    contenido = s[i] if i < len(s) else ''
                    i += 1
                if contenido:
                    tokens.append((kind, contenido))
            else:
                j = i + 1
                while j < len(s) and s[j] not in ('_', '^'):
                    j += 1
                tokens.append(('n', s[i:j]))
                i = j
        return tokens

    def _draw_text_subscript_suffix(self, draw, x, y, main_text, suffix,
                                    font_main, font_sub, fill='black'):
        draw.text((x, y), main_text, fill=fill, font=font_main)
        bbox_main = draw.textbbox((0, 0), main_text, font=font_main)
        w_main = bbox_main[2] - bbox_main[0]
        h_main = bbox_main[3] - bbox_main[1]
        bbox_sub = draw.textbbox((0, 0), suffix, font=font_sub)
        h_sub = bbox_sub[3] - bbox_sub[1]
        y_sub = y + h_main - h_sub
        draw.text((x + w_main + 2, y_sub), suffix, fill=fill, font=font_sub)
        return x + w_main + 2 + (bbox_sub[2] - bbox_sub[0])

    def _draw_formula_with_markup(self, draw, x, y, formula,
                                   font_main, font_sub, font_sup, fill='black'):
        tokens = self._parsear_formula(formula)
        cursor_x = x
        h_main = draw.textbbox((0, 0), 'A', font=font_main)[3]
        for kind, texto in tokens:
            if kind == 'n':
                draw.text((cursor_x, y), texto, fill=fill, font=font_main)
                cursor_x += draw.textbbox((0, 0), texto, font=font_main)[2]
            elif kind == 's':
                h_s = draw.textbbox((0, 0), texto, font=font_sub)[3]
                y_s = y + h_main - h_s
                draw.text((cursor_x, y_s), texto, fill=fill, font=font_sub)
                cursor_x += draw.textbbox((0, 0), texto, font=font_sub)[2]
            elif kind == 'p':
                y_p = y - int(h_main * 0.30)
                draw.text((cursor_x, y_p), texto, fill=fill, font=font_sup)
                cursor_x += draw.textbbox((0, 0), texto, font=font_sup)[2]
        return cursor_x

    # --- Pictogramas ---
    def obtener_pictograma(self, simbolo, tamano):
        clave = f"{simbolo}_{tamano}"
        if clave in self.cache_pictogramas:
            return self.cache_pictogramas[clave]

        img = None
        if self.pictogramas_dir and simbolo in PICTOGRAMAS_OSHA:
            archivo = os.path.join(self.pictogramas_dir, PICTOGRAMAS_OSHA[simbolo])
            if os.path.exists(archivo):
                try:
                    eps_img = Image.open(archivo)
                    base_size = 500
                    w, h = eps_img.size
                    proporcion = base_size / max(w, h)
                    eps_img = eps_img.resize(
                        (int(w * proporcion), int(h * proporcion)),
                        Image.Resampling.LANCZOS
                    )
                    if eps_img.mode != 'RGBA':
                        eps_img = eps_img.convert('RGBA')
                    img = eps_img.resize((tamano, tamano), Image.Resampling.LANCZOS)
                except Exception as e:
                    logger.warning(f"Error procesando EPS {simbolo}: {e}")

        if img is None:
            img = self._generar_pictograma_respaldo(simbolo, tamano)
        self.cache_pictogramas[clave] = img
        return img

    def _generar_pictograma_respaldo(self, simbolo, tamano):
        img = Image.new('RGBA', (tamano, tamano), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        margen = int(tamano * 0.08)
        cx, cy = tamano // 2, tamano // 2
        puntos = [(cx, margen), (tamano - margen, cy),
                  (cx, tamano - margen), (margen, cy)]
        draw.polygon(puntos, fill='white')
        for i in range(3):
            offset = i * 0.8
            draw.polygon([
                (puntos[0][0], puntos[0][1] + offset),
                (puntos[1][0] - offset, puntos[1][1]),
                (puntos[2][0], puntos[2][1] - offset),
                (puntos[3][0] + offset, puntos[3][1])
            ], outline='#C8102E', width=max(2, int(tamano * 0.025)))
        font = obtener_fuente(int(tamano * 0.3), bold=True)
        if "Explosivo" in simbolo:
            draw.ellipse([cx-tamano*0.2, cy-tamano*0.2, cx+tamano*0.2, cy+tamano*0.2], outline='black', width=3)
        elif "Inflamable" in simbolo:
            draw.ellipse([cx-tamano*0.15, cy-tamano*0.25, cx+tamano*0.15, cy+tamano*0.1], fill='#FF6600')
            draw.polygon([(cx, cy-tamano*0.35), (cx-tamano*0.1, cy-tamano*0.1), (cx+tamano*0.1, cy-tamano*0.1)], fill='#FF6600')
        elif "Comburente" in simbolo:
            draw.ellipse([cx-tamano*0.2, cy-tamano*0.2, cx+tamano*0.2, cy+tamano*0.2], outline='black', width=3)
            bbox = draw.textbbox((0,0), "O", font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((cx-tw/2, cy-th/2), "O", fill='black', font=font)
        elif "Gas Comprimido" in simbolo:
            draw.rectangle([cx-tamano*0.2, cy-tamano*0.15, cx+tamano*0.2, cy+tamano*0.2], outline='black', width=2)
        elif "Corrosivo" in simbolo:
            draw.rectangle([cx-tamano*0.25, cy-tamano*0.15, cx-tamano*0.1, cy+tamano*0.2], fill='gray', outline='black')
            draw.rectangle([cx+tamano*0.1, cy-tamano*0.1, cx+tamano*0.25, cy+tamano*0.15], fill='gray', outline='black')
        elif "Tóxico" in simbolo:
            draw.ellipse([cx-tamano*0.2, cy-tamano*0.25, cx-tamano*0.05, cy-tamano*0.1], fill='black')
            draw.ellipse([cx+tamano*0.05, cy-tamano*0.25, cx+tamano*0.2, cy-tamano*0.1], fill='black')
        elif "Irritante" in simbolo:
            draw.rectangle([cx-5, cy-tamano*0.25, cx+5, cy-tamano*0.05], fill='black')
            draw.ellipse([cx-5, cy+tamano*0.05, cx+5, cy+tamano*0.15], fill='black')
        else:
            bbox = draw.textbbox((0,0), simbolo[0] if simbolo else "?", font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text((cx-tw/2, cy-th/2), simbolo[0] if simbolo else "?", fill='black', font=font)
        return img

    # ------------------------------------------------------------------
    # MÉTODO PRINCIPAL – CREAR ETIQUETA
    # ------------------------------------------------------------------
    def crear_etiqueta(self, datos, ancho_mm=70, alto_mm=40, dpi=300):
        """
        Genera una etiqueta GHS como imagen PIL.

        Args:
            datos: dict con campos del reactivo (ver documentación).
            ancho_mm: ancho de la etiqueta en milímetros.
            alto_mm: alto de la etiqueta en milímetros.
            dpi: resolución en puntos por pulgada.

        Returns:
            PIL.Image.Image
        """
        ancho_px = int(ancho_mm * dpi / 25.4)
        alto_px = int(alto_mm * dpi / 25.4)
        img = Image.new('RGB', (ancho_px, alto_px), color='white')
        draw = ImageDraw.Draw(img)
        margen = int(ancho_px * 0.025)
        margen_int = int(ancho_px * 0.015)

        # 1. LOGOS Y TEXTO INSTITUCIONAL
        alto_logo = int(alto_px * 0.16)
        y_logo = margen
        ancho_logo_izq = 0
        x_der = ancho_px - margen

        if self.logo_izq:
            proporcion = alto_logo / self.logo_izq.height
            ancho_logo_izq = int(self.logo_izq.width * proporcion)
            logo_redim = self.logo_izq.resize((ancho_logo_izq, alto_logo), Image.Resampling.LANCZOS)
            if logo_redim.mode == 'RGBA':
                fondo = Image.new('RGB', logo_redim.size, (255, 255, 255))
                fondo.paste(logo_redim, mask=logo_redim.split()[3])
                logo_redim = fondo
            img.paste(logo_redim, (margen, y_logo))

        if self.logo_der:
            proporcion = alto_logo / self.logo_der.height
            ancho_logo_der = int(self.logo_der.width * proporcion)
            logo_redim = self.logo_der.resize((ancho_logo_der, alto_logo), Image.Resampling.LANCZOS)
            if logo_redim.mode == 'RGBA':
                fondo = Image.new('RGB', logo_redim.size, (255, 255, 255))
                fondo.paste(logo_redim, mask=logo_redim.split()[3])
                logo_redim = fondo
            x_der = ancho_px - margen - ancho_logo_der
            img.paste(logo_redim, (x_der, y_logo))

        lineas_institucion = []
        for linea in datos.get('lineas_institucion', []):
            if linea.strip():
                lineas_institucion.append(linea.strip())
        if not lineas_institucion:
            nombre_org = datos.get('organizacion', '')
            if nombre_org:
                lineas_institucion.append(nombre_org)

        if lineas_institucion:
            font_inst = obtener_fuente(int(alto_px * 0.035), bold=True)
            ancho_espacio = (x_der - (margen + ancho_logo_izq)) if self.logo_izq and self.logo_der else (ancho_px - 2 * margen)
            for linea in lineas_institucion:
                bbox = draw.textbbox((0, 0), linea, font=font_inst)
                if bbox[2] - bbox[0] > ancho_espacio:
                    factor = ancho_espacio / (bbox[2] - bbox[0]) * 0.95
                    font_inst = obtener_fuente(max(8, int(int(alto_px * 0.035) * factor)), bold=True)
                    break
            alturas = [draw.textbbox((0, 0), l, font=font_inst)[3] - draw.textbbox((0, 0), l, font=font_inst)[1] for l in lineas_institucion]
            alto_texto = sum(alturas) + (len(alturas) - 1) * (margen_int // 2)
            y_inst = y_logo + (alto_logo - alto_texto) // 2
            for i, linea in enumerate(lineas_institucion):
                bbox = draw.textbbox((0, 0), linea, font=font_inst)
                x_centro = (ancho_px - (bbox[2] - bbox[0])) // 2
                draw.text((x_centro, y_inst), linea, fill='#000000', font=font_inst)
                y_inst += alturas[i] + (margen_int // 2)

        y = y_logo + alto_logo + margen_int
        draw.line([(margen, y), (ancho_px - margen, y)], fill='#CCCCCC', width=1)
        y += margen_int

        # 2. FUENTES
        font_nombre = obtener_fuente(int(alto_px * 0.08), bold=True)
        font_sub_nombre = obtener_fuente(int(alto_px * 0.05), bold=True)
        font_normal = obtener_fuente(int(alto_px * 0.045), bold=False)
        font_sub_normal = obtener_fuente(int(alto_px * 0.029), bold=False)
        font_sup_normal = obtener_fuente(int(alto_px * 0.029), bold=False)
        font_pequena = obtener_fuente(int(alto_px * 0.035), bold=False)
        font_muy_pequena_bold = obtener_fuente(int(alto_px * 0.03), bold=True)
        font_pequena_bold = obtener_fuente(int(alto_px * 0.035), bold=True)
        x = margen

        # 3. NOMBRE
        nombre = datos.get('nombre', 'SIN NOMBRE').upper()
        estado_fisico = datos.get('estado_fisico', '').strip()
        max_ancho = int(ancho_px * 0.85)
        palabras = nombre.split()
        lineas = []
        linea_actual = ""
        for palabra in palabras:
            prueba = linea_actual + " " + palabra if linea_actual else palabra
            bbox = draw.textbbox((0, 0), prueba, font=font_nombre)
            if bbox[2] - bbox[0] <= max_ancho:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual)

        for i, linea in enumerate(lineas[:2]):
            es_ultima = (i == min(len(lineas), 2) - 1)
            if es_ultima and estado_fisico:
                sufijo = "(líq)" if estado_fisico == "l" else f"({estado_fisico})"
                self._draw_text_subscript_suffix(draw, x, y, linea, sufijo, font_nombre, font_sub_nombre)
            else:
                draw.text((x, y), linea, fill='black', font=font_nombre)
            y += int(font_nombre.getbbox(linea)[3] * 1.2)
        y += margen_int // 2

        # 4. FÓRMULA, CAS, CONCENTRACIÓN
        cursor_x = x
        cursor_y = y
        if datos.get('formula'):
            label_f = "Fórmula: "
            draw.text((cursor_x, cursor_y), label_f, fill='#333333', font=font_normal)
            cursor_x += draw.textbbox((0, 0), label_f, font=font_normal)[2]
            cursor_x = self._draw_formula_with_markup(draw, cursor_x, cursor_y, datos['formula'],
                                                       font_normal, font_sub_normal, font_sup_normal, fill='#333333')
            if datos.get('cas'):
                cursor_x += draw.textbbox((0, 0), "   ", font=font_normal)[2]
        if datos.get('cas'):
            label_c = "CAS: "
            draw.text((cursor_x, cursor_y), label_c, fill='#333333', font=font_normal)
            cursor_x += draw.textbbox((0, 0), label_c, font=font_normal)[2]
            draw.text((cursor_x, cursor_y), datos['cas'], fill='#333333', font=font_normal)
        y = cursor_y + int(font_normal.getbbox("A")[3] + margen_int * 0.8)

        # 5. PICTOGRAMAS Y QR
        simbolos = datos.get('simbolos', [])
        tam_picto = int(alto_px * 0.15)
        tamano_qr = int(alto_px * 0.20)

        qr_url = datos.get('qr_url', '')
        if qr_url:
            qr_obj = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
                                    box_size=12, border=1)
            qr_obj.add_data(qr_url)
            qr_obj.make(fit=True)
            qr_img = qr_obj.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((tamano_qr, tamano_qr), Image.Resampling.LANCZOS)
            if qr_img.mode != 'RGB':
                qr_img = qr_img.convert('RGB')
            img.paste(qr_img, (ancho_px - margen - tamano_qr, y))

        if simbolos:
            x_picto = x
            for simb in simbolos[:5]:
                picto = self.obtener_pictograma(simb, tam_picto)
                img.paste(picto, (x_picto, y), picto)
                x_picto += tam_picto + int(margen_int * 0.5)

        alto_bloque = max(tam_picto if simbolos else 0, tamano_qr if qr_url else 0)
        y += alto_bloque + margen_int if alto_bloque else 0

        # 6. PALABRA DE ADVERTENCIA
        palabra = datos.get('palabra_advertencia', '')
        if palabra:
            color = '#C8102E' if palabra == 'PELIGRO' else '#FFA500'
            draw.text((x, y), palabra, fill=color, font=font_nombre)
            y += int(font_nombre.getbbox(palabra)[3] + margen_int * 0.8)

        # 7. H-CODES
        if datos.get('frases_peligro'):
            codigos_h = re.findall(r'H\d{3}(?:\d{2})?', datos['frases_peligro'])
            if codigos_h:
                draw.text((x, y), "Peligros: " + ", ".join(codigos_h[:5]), fill='black', font=font_pequena)
                y += int(font_pequena.getbbox("A")[3] + margen_int * 0.5)

        # 8. P-CODES
        if datos.get('consejos_prudencia'):
            codigos_p = re.findall(r'P\d{3}(?:\d{2})?', datos['consejos_prudencia'])
            if codigos_p:
                draw.text((x, y), "Prudencia: " + ", ".join(codigos_p[:5]), fill='black', font=font_pequena)
                y += int(font_pequena.getbbox("A")[3] + margen_int * 0.5)

        # 9. PIE
        y_pie = alto_px - int(alto_px * 0.09)
        textos_pie = []
        if datos.get('lote'):
            textos_pie.append(f"Lote: {datos['lote']}")
        if datos.get('fecha_caducidad'):
            textos_pie.append(f"Caducidad: {datos['fecha_caducidad']}")
        if datos.get('cantidad'):
            textos_pie.append(f"Cantidad: {datos['cantidad']}")
        if textos_pie:
            texto_unido = "  •  ".join(textos_pie)
            draw.text((margen, y_pie), texto_unido, fill='#444444', font=font_muy_pequena_bold)

        # 10. MARCO
        palabra_borde = (datos.get('palabra_advertencia', '') or '').upper()
        if 'PELIGRO' in palabra_borde:
            color_borde = '#CD1719'
            grosor = max(4, int(min(ancho_px, alto_px) * 0.012))
        elif 'ATENCI' in palabra_borde:
            color_borde = '#034991'
            grosor = max(4, int(min(ancho_px, alto_px) * 0.012))
        else:
            color_borde = '#a7a7a9'
            grosor = max(3, int(min(ancho_px, alto_px) * 0.008))
        for offset in range(grosor):
            draw.rectangle([offset, offset, ancho_px - 1 - offset, alto_px - 1 - offset],
                           outline=color_borde)

        return img

    def crear_etiqueta_bytes(self, datos, ancho_mm=70, alto_mm=40, dpi=300, formato='PNG'):
        """Genera la etiqueta y retorna bytes del archivo de imagen."""
        img = self.crear_etiqueta(datos, ancho_mm, alto_mm, dpi)
        buf = io.BytesIO()
        img.save(buf, format=formato)
        buf.seek(0)
        return buf.getvalue()


def generar_datos_desde_sustancia(substance):
    """
    Convierte una instancia de sga.models.Substance a un dict
    compatible con LabelGenerator.crear_etiqueta().
    """
    from sga.models import SGAComplement

    datos = {
        'nombre': substance.comercial_name or substance.uipa_name or '',
        'formula': '',
        'cas': '',
        'simbolos': [],
        'palabra_advertencia': '',
        'frases_peligro': '',
        'consejos_prudencia': '',
    }

    # SubstanceCharacteristics
    try:
        chars = substance.substancecharacteristics
        datos['formula'] = chars.molecular_formula or ''
        datos['cas'] = chars.cas_id_number or ''
    except Exception:
        pass

    # H-codes desde danger_indications
    h_codes = []
    warning_words = []
    for di in substance.danger_indications.all():
        h_codes.append(di.code)
        if di.warning_words:
            warning_words.append(di.warning_words)

    datos['frases_peligro'] = "\n".join(
        f"{di.code} - {di.description}" for di in substance.danger_indications.all()
    )

    # P-codes desde SGAComplement o danger_indications.prudence_advice
    p_codes = set()
    for di in substance.danger_indications.all():
        for pa in di.prudence_advice.all():
            p_codes.add((pa.code, pa.name))

    # También de SGAComplement si existe
    try:
        complement = SGAComplement.objects.filter(substance=substance).first()
        if complement:
            for pa in complement.prudence_advice.all():
                p_codes.add((pa.code, pa.name))
            if complement.warningword:
                warning_words.append(complement.warningword)
    except Exception:
        pass

    datos['consejos_prudencia'] = "\n".join(f"{code} - {name}" for code, name in sorted(p_codes))

    # Pictogramas
    datos['simbolos'] = resolver_pictogramas([di.code for di in substance.danger_indications.all()])

    # Palabra de advertencia
    if warning_words:
        datos['palabra_advertencia'] = resolver_palabra_advertencia(warning_words)

    return datos
