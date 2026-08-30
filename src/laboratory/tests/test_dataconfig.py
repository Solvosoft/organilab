# encoding: utf-8
"""Pruebas del módulo canónico de ``Furniture.dataconfig``.

Dos mitades, igual que el módulo: las funciones puras se prueban sin base de
datos, y ``DataconfigService`` contra un mueble real del fixture.

El eje de casi todo es que **las filas son irregulares a propósito**: una fila
de dos celdas y otra de cuatro conviven, y ningún camino puede rellenarlas
hasta un rectángulo sin mentir sobre la forma del laboratorio.
"""

import json

from django.apps import apps
from django.test import TestCase

from laboratory import dataconfig
from laboratory.forms import FurnitureForm
from laboratory.models import Furniture


IRREGULAR = [[[6], []], [[], [], [5], []]]


class DataconfigParseTest(TestCase):
    """``parse`` es tolerante: la base de datos tiene tres formatos históricos."""

    def test_reads_the_canonical_json(self):
        self.assertEqual(
            dataconfig.parse('[[[],[2]],[[1],[]]]'), [[[], [2]], [[1], []]]
        )

    def test_reads_the_python_repr_the_old_writers_produced(self):
        # ``str(dataconfig)`` escribía comillas simples, que no son JSON.
        self.assertEqual(
            dataconfig.parse("[[[], [2]], [[1], []]]"), [[[], [2]], [[1], []]]
        )
        self.assertEqual(dataconfig.parse("[['1', '2']]"), [[[1], [2]]])

    def test_reads_a_legacy_int_cell(self):
        # Regresión: el escritor antiguo trataba la celda como si siempre fuera
        # una lista y reventaba con ``AttributeError`` cuando era un entero.
        self.assertEqual(dataconfig.parse("[[1,2],[3]]"), [[[1], [2]], [[3]]])

    def test_reads_a_csv_cell(self):
        self.assertEqual(dataconfig.parse('[["1,2", "3"]]'), [[[1, 2], [3]]])

    def test_empty_input_is_an_empty_grid(self):
        for value in ("", None, [], "   "):
            with self.subTest(value=value):
                self.assertEqual(dataconfig.parse(value), [])

    def test_garbage_is_an_empty_grid_instead_of_an_exception(self):
        # Leer la base de datos nunca puede reventar: quien valida entrada nueva
        # es ``parse_strict``.
        for value in ("not json", "{}", '{"a": 1}', "42"):
            with self.subTest(value=value):
                self.assertEqual(dataconfig.parse(value), [])

    def test_a_degenerate_row_is_read_as_a_single_cell_row(self):
        self.assertEqual(dataconfig.parse("[1, [2]]"), [[[1]], [[2]]])

    def test_irregular_rows_are_preserved(self):
        text = dataconfig.dump(IRREGULAR)
        self.assertEqual(dataconfig.parse(text), IRREGULAR)
        self.assertEqual(dataconfig.dimensions(dataconfig.parse(text)), (2, [2, 4]))

    def test_a_repeated_shelf_stays_in_its_first_position(self):
        # Un estante ocupa una posición; los duplicados son daño de los
        # escritores antiguos.
        self.assertEqual(
            dataconfig.parse("[[[7],[7]],[[7],[8]]]"), [[[7], []], [[], [8]]]
        )

    def test_dedupe_can_be_switched_off(self):
        self.assertEqual(
            dataconfig.parse("[[[7],[7]]]", dedupe=False), [[[7], [7]]]
        )


class DataconfigDumpTest(TestCase):

    def test_dump_is_compact(self):
        # Sin espacios: exactamente lo que producía el editor en JavaScript, de
        # modo que la migración no toca las filas que ya estaban bien.
        self.assertEqual(dataconfig.dump(IRREGULAR), "[[[6],[]],[[],[],[5],[]]]")

    def test_dump_writes_integers_even_from_strings(self):
        self.assertEqual(dataconfig.dump([[["3"]]]), "[[[3]]]")

    def test_dump_never_emits_single_quotes(self):
        # El otro lado del bug histórico: ``str(dataconfig)`` producía JSON
        # inválido y el parser tolerante lo tapaba.  Escribir es estricto.
        text = dataconfig.dump(dataconfig.parse("[['1', '2'], ['3']]"))
        self.assertNotIn("'", text)
        self.assertEqual(json.loads(text), [[[1], [2]], [[3]]])

    def test_normalize_is_idempotent(self):
        once = dataconfig.normalize("[[[6], []], [[], [], [5], []]]")
        self.assertEqual(once, "[[[6],[]],[[],[],[5],[]]]")
        self.assertEqual(dataconfig.normalize(once), once)


class DataconfigStrictTest(TestCase):
    """``parse_strict`` valida entrada nueva: aceptar basura es perderla."""

    def test_accepts_a_valid_grid(self):
        self.assertEqual(dataconfig.parse_strict("[[[1],[]]]"), [[[1], []]])

    def test_accepts_a_csv_cell(self):
        self.assertEqual(dataconfig.parse_strict('[["1,2"]]'), [[[1, 2]]])

    def test_empty_is_an_empty_grid(self):
        for value in ("", "   ", None):
            with self.subTest(value=value):
                self.assertEqual(dataconfig.parse_strict(value), [])

    def test_rejects_what_parse_would_swallow(self):
        for value in ("not json", "{}", "42", "[[true]]", '[["x"]]', "[1]"):
            with self.subTest(value=value):
                with self.assertRaises(dataconfig.DataconfigInvalid):
                    dataconfig.parse_strict(value)


class DataconfigHelpersTest(TestCase):

    def test_iter_shelf_pks_reads_in_order(self):
        self.assertEqual(dataconfig.iter_shelf_pks(IRREGULAR), [6, 5])

    def test_get_position_finds_the_shelf(self):
        self.assertEqual(dataconfig.get_position(IRREGULAR, 5), (1, 2))
        self.assertEqual(dataconfig.get_position(IRREGULAR, "6"), (0, 0))

    def test_get_position_of_an_absent_or_invalid_shelf(self):
        self.assertEqual(dataconfig.get_position(IRREGULAR, 99), (None, None))
        self.assertEqual(dataconfig.get_position(IRREGULAR, "x"), (None, None))

    def test_dimensions_reports_the_width_of_each_row(self):
        self.assertEqual(dataconfig.dimensions(IRREGULAR), (2, [2, 4]))
        self.assertEqual(dataconfig.dimensions([]), (0, []))

    def test_max_width(self):
        self.assertEqual(dataconfig.max_width(IRREGULAR), 4)
        self.assertEqual(dataconfig.max_width([]), 0)

    def test_remove_shelf_from_matrix(self):
        matrix = [[[6], []], [[], [], [5], []]]
        self.assertTrue(dataconfig.remove_shelf_from_matrix(matrix, 5))
        self.assertEqual(matrix, [[[6], []], [[], [], [], []]])
        self.assertFalse(dataconfig.remove_shelf_from_matrix(matrix, 99))


class DataconfigServiceTest(TestCase):
    """La mutación, contra un mueble real.  El fixture ya trae rejillas irregulares."""

    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.furniture = Furniture.objects.get(pk=2)
        self.assertEqual(self.furniture.get_grid(), IRREGULAR)

    def service(self):
        return dataconfig.DataconfigService(self.furniture)

    def grid(self):
        return Furniture.objects.get(pk=self.furniture.pk).get_grid()

    # -- estantes ----------------------------------------------------------

    def test_place_shelf_grows_the_row_it_needs(self):
        self.service().place_shelf(13, 0, 3)
        self.assertEqual(self.grid(), [[[6], [], [], [13]], [[], [], [5], []]])

    def test_place_shelf_grows_the_matrix_downwards(self):
        self.service().place_shelf(13, 3, 0)
        self.assertEqual(len(self.grid()), 4)
        self.assertEqual(dataconfig.get_position(self.grid(), 13), (3, 0))

    def test_a_shelf_only_ever_has_one_position(self):
        self.service().place_shelf(5, 0, 1)
        self.assertEqual(self.grid(), [[[6], [5]], [[], [], [], []]])
        self.assertEqual(dataconfig.iter_shelf_pks(self.grid()).count(5), 1)

    def test_move_shelf_is_place_shelf(self):
        self.service().move_shelf(6, 1, 3)
        self.assertEqual(dataconfig.get_position(self.grid(), 6), (1, 3))

    def test_a_negative_position_is_refused(self):
        with self.assertRaises(dataconfig.DataconfigConflict):
            self.service().place_shelf(13, -1, 0)

    def test_remove_shelf_leaves_the_shape_alone(self):
        self.service().remove_shelf(5)
        self.assertEqual(self.grid(), [[[6], []], [[], [], [], []]])

    def test_the_stored_text_is_canonical(self):
        self.service().remove_shelf(6)
        stored = Furniture.objects.get(pk=self.furniture.pk).dataconfig
        self.assertEqual(stored, "[[[],[]],[[],[],[5],[]]]")

    def test_the_callers_instance_stays_coherent(self):
        self.service().remove_shelf(6)
        self.assertEqual(self.furniture.get_grid(), [[[], []], [[], [], [5], []]])

    # -- filas -------------------------------------------------------------

    def test_add_row_is_as_wide_as_the_longest_row(self):
        self.service().add_row()
        self.assertEqual(dataconfig.dimensions(self.grid()), (3, [2, 4, 4]))

    def test_add_row_accepts_an_explicit_width(self):
        self.service().add_row(cells=2)
        self.assertEqual(dataconfig.dimensions(self.grid()), (3, [2, 4, 2]))

    def test_add_row_at_an_index(self):
        self.service().add_row(index=0, cells=1)
        self.assertEqual(dataconfig.dimensions(self.grid()), (3, [1, 2, 4]))

    def test_remove_an_empty_row(self):
        self.service().add_row()
        self.service().remove_row(2)
        self.assertEqual(self.grid(), IRREGULAR)

    def test_removing_an_occupied_row_is_refused_and_says_which_shelves(self):
        with self.assertRaises(dataconfig.DataconfigConflict) as caught:
            self.service().remove_row(1)
        self.assertEqual(caught.exception.shelves, [5])
        self.assertEqual(self.grid(), IRREGULAR)

    def test_removing_a_row_that_does_not_exist_is_refused(self):
        with self.assertRaises(dataconfig.DataconfigConflict):
            self.service().remove_row(9)

    # -- columnas ----------------------------------------------------------

    def test_add_col_preserves_the_irregularity(self):
        # Una fila más corta que el índice recibe su celda al final: no se
        # rellena hasta alcanzar a las demás.
        self.service().add_col(index=3)
        self.assertEqual(dataconfig.dimensions(self.grid()), (2, [3, 5]))

    def test_add_col_without_an_index_appends_to_every_row(self):
        self.service().add_col()
        self.assertEqual(dataconfig.dimensions(self.grid()), (2, [3, 5]))

    def test_add_col_on_an_empty_grid_creates_one_cell(self):
        empty = Furniture.objects.get(pk=1)
        empty.dataconfig = ""
        empty.save()
        dataconfig.DataconfigService(empty).add_col()
        self.assertEqual(Furniture.objects.get(pk=1).get_grid(), [[[]]])

    def test_remove_col_only_shrinks_the_rows_that_have_that_position(self):
        self.service().remove_col(index=3)
        self.assertEqual(dataconfig.dimensions(self.grid()), (2, [2, 3]))

    def test_remove_col_without_an_index_drops_the_last_cell_of_each_row(self):
        self.service().remove_col()
        self.assertEqual(dataconfig.dimensions(self.grid()), (2, [1, 3]))

    def test_removing_an_occupied_column_is_refused_and_says_which_shelves(self):
        with self.assertRaises(dataconfig.DataconfigConflict) as caught:
            self.service().remove_col(index=2)
        self.assertEqual(caught.exception.shelves, [5])
        self.assertEqual(self.grid(), IRREGULAR)

    def test_removing_a_column_no_row_has_is_refused(self):
        with self.assertRaises(dataconfig.DataconfigConflict):
            self.service().remove_col(index=9)


class DataconfigRegressionTest(TestCase):
    """Los bugs concretos que motivaron el módulo, cada uno con su nombre."""

    fixtures = ["laboratory_data.json"]

    def furniture(self):
        return Furniture.objects.get(pk=1)

    def test_removing_a_shelf_from_an_int_cell_does_not_crash(self):
        """El escritor viejo trataba la celda como lista y reventaba si era int.

        ``models.py`` hacía ``val = [col]; val.set("")`` sobre la rama del
        formato legacy, que es un ``AttributeError`` en cuanto la celda venía
        como entero suelto.
        """
        furniture = self.furniture()
        furniture.dataconfig = "[[1,2],[3]]"
        furniture.save()

        furniture.remove_shelf_dataconfig(1)

        self.assertEqual(self.furniture().get_grid(), [[[], [2]], [[3]]])

    def test_a_dataconfig_written_by_the_old_str_becomes_valid_json(self):
        furniture = self.furniture()
        furniture.dataconfig = "[['1', '2'], ['3']]"
        furniture.save()

        furniture.change_shelf_dataconfig(1, 0, 4)

        stored = self.furniture().dataconfig
        self.assertNotIn("'", stored)
        # Una celda guarda una lista: colocar en una ocupada añade, no sustituye.
        self.assertEqual(json.loads(stored), [[[1], [2]], [[3, 4]]])

    def test_get_position_shelf_still_returns_a_list(self):
        # Contrato que consume el código viejo, vivo hasta que se retire.
        furniture = self.furniture()
        furniture.dataconfig = dataconfig.dump(IRREGULAR)
        furniture.save()
        self.assertEqual(furniture.get_position_shelf(5), [1, 2])
        self.assertEqual(furniture.get_position_shelf(99), [None, None])

    def test_resolve_shelves_takes_one_query_and_drops_dead_pks(self):
        matrix = [[[1], [9999]], [[2], []]]
        with self.assertNumQueries(1):
            resolved = dataconfig.resolve_shelves(matrix)
        self.assertEqual([[len(cell) for cell in row] for row in resolved],
                         [[1, 0], [1, 0]])

    def test_a_refused_operation_writes_nothing(self):
        furniture = self.furniture()
        furniture.dataconfig = dataconfig.dump(IRREGULAR)
        furniture.save()
        before = self.furniture().dataconfig

        with self.assertRaises(dataconfig.DataconfigConflict):
            dataconfig.DataconfigService(furniture).remove_row(1)

        self.assertEqual(self.furniture().dataconfig, before)


class DataconfigMigrationTest(TestCase):
    """La migración de datos converge los formatos históricos y es idempotente."""

    fixtures = ["laboratory_data.json"]

    def normalize(self):
        module = __import__(
            "laboratory.migrations.0223_normalize_dataconfig",
            fromlist=["normalize"],
        )
        module.normalize(apps, None)

    def test_every_historical_format_converges_to_the_canonical_one(self):
        historical = {
            1: "[['1', '2'], ['3']]",       # repr de Python
            2: '[["1,2"],["3"]]',           # celdas CSV
            3: "[[1,2],[3]]",               # enteros sueltos
            4: "[[[1],[2]],[[3],[],[],[]]]",  # ya canónico
        }
        for pk, text in historical.items():
            Furniture.objects.filter(pk=pk).update(dataconfig=text)

        self.normalize()

        for pk in historical:
            with self.subTest(furniture=pk):
                stored = Furniture.objects.get(pk=pk).dataconfig
                self.assertNotIn("'", stored)
                self.assertNotIn(" ", stored)
                self.assertEqual(stored, dataconfig.normalize(stored))

    def test_a_second_pass_changes_nothing(self):
        self.normalize()
        first = dict(Furniture.objects.values_list("pk", "dataconfig"))
        self.normalize()
        self.assertEqual(dict(Furniture.objects.values_list("pk", "dataconfig")), first)

    def test_the_irregular_shape_survives_the_migration(self):
        self.normalize()
        self.assertEqual(Furniture.objects.get(pk=2).get_grid(), IRREGULAR)


class FurnitureFormDataconfigTest(TestCase):
    """El formulario valida entrada nueva: aceptar basura es borrar el mueble."""

    fixtures = ["laboratory_data.json"]

    def form(self, dataconfig_value):
        furniture = Furniture.objects.get(pk=2)
        return FurnitureForm(
            data={
                "labroom": furniture.labroom_id,
                "name": furniture.name,
                "type": furniture.type_id,
                "color": furniture.color,
                "dataconfig": dataconfig_value,
                "shelfs": "",
            }
        )

    def test_a_valid_grid_is_stored_canonical(self):
        form = self.form("[[[6], []], [[], [], [5], []]]")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["dataconfig"], "[[[6],[]],[[],[],[5],[]]]")

    def test_the_legacy_repr_is_accepted_and_normalized(self):
        form = self.form("[['1', '2']]")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["dataconfig"], "[[[1],[2]]]")

    def test_garbage_is_refused_instead_of_wiping_the_furniture(self):
        """Regresión: ``parse_strict`` devolvía ``[]`` ante texto ilegible.

        El formulario lo guardaba como cuadrícula vacía, así que un
        ``dataconfig`` corrupto borraba en silencio la distribución entera del
        mueble en vez de dar error.
        """
        for value in ("not json", "&&&", "[[[1],[]]"):
            with self.subTest(value=value):
                form = self.form(value)
                self.assertFalse(form.is_valid())
                self.assertIn("dataconfig", form.errors)
