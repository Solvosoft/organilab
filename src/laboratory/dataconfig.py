# encoding: utf-8
"""Único dueño del formato de ``Furniture.dataconfig``.

``dataconfig`` codifica la distribución física de un mueble: una matriz de
filas, cada fila con sus celdas, cada celda con la lista de pks de los
estantes que ocupan esa posición.

**Las filas son irregulares a propósito**: la forma la define el usuario según
cómo sea su laboratorio, así que una fila puede tener dos celdas y la siguiente
cuatro.  Ni al leer ni al escribir se rellena la matriz hasta un rectángulo.

El módulo se divide en dos mitades con asimetría deliberada:

* **Funciones puras** — ``parse`` es tolerante (la base de datos contiene tres
  formatos históricos: JSON de listas, celdas CSV ``"1,2"`` y el ``repr`` de
  Python con comillas simples), mientras que ``dump`` es estricto (siempre
  ``json.dumps`` de listas de enteros).  Leer flexible y escribir canónico es
  lo que permite converger el formato sin una migración bloqueante.
* **``DataconfigService``** — la mutación, una operación por llamada, cada una
  atómica y con ``select_for_update`` sobre el mueble.

Regla de la capa: ningún otro módulo vuelve a hacer ``json.loads``,
``split(",")`` o ``re.findall`` sobre ``dataconfig``.
"""

import ast
import json

from django.apps import apps
from django.db import transaction
from django.utils.translation import gettext_lazy as _


class DataconfigConflict(Exception):
    """La operación destruiría estantes existentes.

    La API la traduce a ``409 Conflict``: eliminar una fila o una columna que
    contiene estantes se rechaza con motivo en vez de corromper el layout.
    """

    def __init__(self, message, shelves=None):
        super().__init__(message)
        self.message = message
        self.shelves = list(shelves or [])


def _cell_to_pks(cell):
    """Normaliza una celda de cualquier formato histórico a lista de enteros."""
    if cell is None or isinstance(cell, bool):
        return []
    if isinstance(cell, int):
        return [cell]
    if isinstance(cell, float):
        return [int(cell)]
    if isinstance(cell, str):
        pks = []
        for part in cell.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                pks.append(int(part))
            except (TypeError, ValueError):
                continue
        return pks
    if isinstance(cell, (list, tuple)):
        pks = []
        for item in cell:
            pks.extend(_cell_to_pks(item))
        return pks
    return []


#: Lo que devuelve :func:`_deserialize` cuando el texto no es deserializable.
#: Hace falta un centinela porque ``[]`` es un valor legítimo: sin él,
#: ``parse_strict`` no podría distinguir una cuadrícula vacía de basura, y
#: aceptaría en silencio un ``dataconfig`` corrupto borrando el mueble entero.
UNPARSEABLE = object()


def _deserialize(text):
    """JSON, o el ``repr`` de Python, o :data:`UNPARSEABLE`."""
    if isinstance(text, (list, tuple)):
        return list(text)
    if not text:
        return []
    if not isinstance(text, str):
        return UNPARSEABLE
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    try:
        # El legado escribía ``str(dataconfig)``: comillas simples, JSON inválido.
        return ast.literal_eval(text)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return UNPARSEABLE


def _loads(text):
    """Deserializa tolerando JSON, el ``repr`` de Python y la basura."""
    data = _deserialize(text)
    return [] if data is UNPARSEABLE else data


def parse(text, dedupe=True):
    """``dataconfig`` -> matriz ``filas -> celdas -> [pk de Shelf]``.

    Preserva filas irregulares.  Con ``dedupe`` (por defecto) un mismo estante
    se queda solo en su primera posición: un estante ocupa una posición, y los
    duplicados son daño de los escritores antiguos.
    """
    data = _loads(text)
    if not isinstance(data, (list, tuple)):
        return []

    matrix, seen = [], set()
    for row in data:
        if not isinstance(row, (list, tuple)):
            # Fila degenerada: la tratamos como una fila de una sola celda.
            row = [row]
        cells = []
        for cell in row:
            pks = []
            for pk in _cell_to_pks(cell):
                if dedupe:
                    if pk in seen:
                        continue
                    seen.add(pk)
                pks.append(pk)
            cells.append(pks)
        matrix.append(cells)
    return matrix


def dump(matrix):
    """Matriz -> texto canónico: JSON compacto de listas de enteros.

    Sin espacios, que es exactamente lo que venía produciendo el editor en
    JavaScript: así la migración de datos no toca las filas que ya estaban
    bien.
    """
    return json.dumps(
        [[[int(pk) for pk in cell] for cell in row] for row in matrix],
        separators=(",", ":"),
    )


class DataconfigInvalid(ValueError):
    """El texto no es una cuadrícula válida.

    Sólo se usa al **aceptar entrada nueva**: leer la base de datos es
    tolerante a propósito, escribir no.
    """


def parse_strict(text):
    """Como :func:`parse`, pero rechaza cualquier cosa que no sea entera.

    ``parse`` es tolerante porque la base de datos contiene formatos
    históricos; ``parse_strict`` es lo que valida un formulario, donde aceptar
    basura sólo sirve para perderla en silencio.
    """
    if not text or (isinstance(text, str) and not text.strip()):
        return []
    data = _deserialize(text)
    if data is UNPARSEABLE or not isinstance(data, (list, tuple)):
        raise DataconfigInvalid(_("Invalid format in shelf dataconfig "))

    matrix = []
    for row in data:
        if not isinstance(row, (list, tuple)):
            raise DataconfigInvalid(_("Invalid format in shelf dataconfig "))
        cells = []
        for cell in row:
            pks = []
            for token in cell if isinstance(cell, (list, tuple)) else [cell]:
                if isinstance(token, bool):
                    raise DataconfigInvalid(_("Invalid format in shelf dataconfig "))
                if isinstance(token, int):
                    pks.append(token)
                    continue
                if isinstance(token, str):
                    for part in token.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        try:
                            pks.append(int(part))
                        except (TypeError, ValueError):
                            raise DataconfigInvalid(
                                _("Invalid format in shelf dataconfig ")
                            )
                    continue
                raise DataconfigInvalid(_("Invalid format in shelf dataconfig "))
            cells.append(pks)
        matrix.append(cells)
    return matrix


def normalize(text):
    """``dump(parse(text))``.  Lo que aplica la migración de datos."""
    return dump(parse(text))


def iter_shelf_pks(matrix):
    """Todos los pks de la matriz, en orden de lectura."""
    return [pk for row in matrix for cell in row for pk in cell]


def get_position(matrix, shelf_pk):
    """``(fila, columna)`` del estante, o ``(None, None)`` si no está."""
    try:
        shelf_pk = int(shelf_pk)
    except (TypeError, ValueError):
        return None, None
    for irow, row in enumerate(matrix):
        for icol, cell in enumerate(row):
            if shelf_pk in cell:
                return irow, icol
    return None, None


def dimensions(matrix):
    """``(número de filas, [ancho de cada fila])``."""
    return len(matrix), [len(row) for row in matrix]


def max_width(matrix):
    """Ancho de la fila más larga (0 si la matriz está vacía)."""
    return max((len(row) for row in matrix), default=0)


def resolve_shelves(matrix):
    """Matriz de pks -> matriz de instancias ``Shelf``, en una sola consulta.

    Los pks que ya no existen se descartan silenciosamente, igual que hacía el
    código anterior.
    """
    pks = set(iter_shelf_pks(matrix))
    if not pks:
        return [[[] for _ in row] for row in matrix]

    Shelf = apps.get_model("laboratory", "Shelf")
    shelves = {shelf.pk: shelf for shelf in Shelf.objects.filter(pk__in=pks)}
    return [
        [[shelves[pk] for pk in cell if pk in shelves] for cell in row]
        for row in matrix
    ]


def remove_shelf_from_matrix(matrix, shelf_pk):
    """Quita el estante de la matriz (in-place).  Devuelve si estaba."""
    shelf_pk = int(shelf_pk)
    found = False
    for row in matrix:
        for cell in row:
            while shelf_pk in cell:
                cell.remove(shelf_pk)
                found = True
    return found


class DataconfigService:
    """Mutación de la cuadrícula, una operación por llamada.

    Cada método abre una transacción con ``select_for_update`` sobre el mueble,
    re-parsea, muta y vuelve a escribir: dos usuarios editando el mismo mueble
    se serializan en la base de datos en vez de competir por sobrescribir un
    string entero.  No existe un estado intermedio que se pueda perder.
    """

    def __init__(self, furniture):
        self.furniture = furniture

    # -- infraestructura ---------------------------------------------------

    def _apply(self, mutate):
        Furniture = apps.get_model("laboratory", "Furniture")
        with transaction.atomic():
            furniture = Furniture.objects.select_for_update().get(
                pk=self.furniture.pk
            )
            matrix = parse(furniture.dataconfig)
            mutate(matrix)
            furniture.dataconfig = dump(matrix)
            furniture.save()
            # Mantiene coherente la instancia que trae el llamador.
            self.furniture.dataconfig = furniture.dataconfig
            return matrix

    def get_matrix(self):
        return parse(self.furniture.dataconfig)

    # -- estantes ----------------------------------------------------------

    def place_shelf(self, shelf_pk, row, col):
        """Coloca el estante en ``(row, col)``, creciendo la matriz si hace falta.

        Un estante tiene una sola posición, así que primero se quita de donde
        estuviera.  La matriz crece porque el usuario puede colocar en una fila
        más corta que las demás: la forma la define él.
        """
        shelf_pk, row, col = int(shelf_pk), int(row), int(col)
        if row < 0 or col < 0:
            raise DataconfigConflict(_("Invalid position"))

        def mutate(matrix):
            remove_shelf_from_matrix(matrix, shelf_pk)
            while len(matrix) <= row:
                matrix.append([])
            while len(matrix[row]) <= col:
                matrix[row].append([])
            matrix[row][col].append(shelf_pk)

        return self._apply(mutate)

    def move_shelf(self, shelf_pk, row, col):
        """Mueve el estante.  Misma semántica que ``place_shelf``."""
        return self.place_shelf(shelf_pk, row, col)

    def remove_shelf(self, shelf_pk):
        """Quita el estante de la cuadrícula (no borra el objeto ``Shelf``)."""
        shelf_pk = int(shelf_pk)
        return self._apply(lambda matrix: remove_shelf_from_matrix(matrix, shelf_pk))

    # -- filas -------------------------------------------------------------

    def add_row(self, index=None, cells=None):
        """Añade una fila.  Por defecto tan ancha como la fila más larga."""

        def mutate(matrix):
            width = cells if cells is not None else max_width(matrix)
            width = max(int(width), 1)
            new_row = [[] for _ in range(width)]
            position = len(matrix) if index is None else int(index)
            position = max(0, min(position, len(matrix)))
            matrix.insert(position, new_row)

        return self._apply(mutate)

    def remove_row(self, index):
        """Elimina la fila.  409 si contiene estantes."""
        index = int(index)

        def mutate(matrix):
            if not (0 <= index < len(matrix)):
                raise DataconfigConflict(_("The row does not exist"))
            occupied = [pk for cell in matrix[index] for pk in cell]
            if occupied:
                raise DataconfigConflict(
                    _("The row still contains shelves"), shelves=occupied
                )
            del matrix[index]

        return self._apply(mutate)

    # -- columnas ----------------------------------------------------------

    def add_col(self, index=None):
        """Añade una celda en esa posición a todas las filas.

        Sobre filas irregulares la irregularidad se preserva: una fila más
        corta que ``index`` recibe su celda al final, no se rellena hasta
        alcanzar a las demás.
        """

        def mutate(matrix):
            if not matrix:
                matrix.append([[]])
                return
            for row in matrix:
                position = len(row) if index is None else int(index)
                position = max(0, min(position, len(row)))
                row.insert(position, [])

        return self._apply(mutate)

    def remove_col(self, index=None):
        """Elimina esa columna de todas las filas que la tengan.  409 si hay estantes."""

        def mutate(matrix):
            targets = {}
            for irow, row in enumerate(matrix):
                position = len(row) - 1 if index is None else int(index)
                if 0 <= position < len(row):
                    targets[irow] = position
            if not targets:
                raise DataconfigConflict(_("The column does not exist"))

            occupied = [pk for irow, icol in targets.items() for pk in matrix[irow][icol]]
            if occupied:
                raise DataconfigConflict(
                    _("The column still contains shelves"), shelves=occupied
                )
            for irow, icol in targets.items():
                del matrix[irow][icol]

        return self._apply(mutate)
