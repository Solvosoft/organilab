import importlib
from datetime import timedelta

from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from laboratory.admin import OrganizationWithChildrenFilter
from laboratory.logsustances import log_object_change
from laboratory.models import Laboratory, ObjectLogChange, OrganizationStructure, ShelfObject

migration = importlib.import_module("laboratory.migrations.0226_delete_root_copies_objectlogchange")


class ObjectLogOrganizationTest(TestCase):
    fixtures = ["laboratory_data.json"]

    def setUp(self):
        self.user = User.objects.get(username="admin")
        self.root = OrganizationStructure.objects.get(pk=1)
        self.child = OrganizationStructure.objects.create(name="Hija", parent=self.root)
        self.grandchild = OrganizationStructure.objects.create(name="Nieta", parent=self.child)
        self.lab = Laboratory.objects.get(pk=1)
        self.shelfobject = ShelfObject.objects.get(pk=1)
        ObjectLogChange.objects.all().delete()

    def log(self, organization, old=5, new=3):
        log_object_change(
            self.user, self.lab.pk, self.shelfobject, old, new, "", 2, organization=organization
        )
        return ObjectLogChange.objects.order_by("pk").last()

    def root_copy(self, original):
        copy = ObjectLogChange.objects.create(
            object=original.object,
            laboratory=original.laboratory,
            user=original.user,
            old_value=original.old_value,
            new_value=original.new_value,
            diff_value=original.diff_value,
            measurement_unit=original.measurement_unit,
            type_action=original.type_action,
            organization_where_action_taken=self.root,
        )
        ObjectLogChange.objects.filter(pk=copy.pk).update(
            update_time=original.update_time + timedelta(milliseconds=8)
        )
        return copy

    def test_movimiento_en_organizacion_hija_se_guarda_una_vez(self):
        self.log(self.child)
        self.assertEqual(ObjectLogChange.objects.count(), 1)
        self.assertEqual(ObjectLogChange.objects.get().organization_where_action_taken, self.child)

    def test_migracion_borra_solo_las_copias_de_la_raiz(self):
        en_hija = self.log(self.child)
        copia_hija = self.root_copy(en_hija)
        en_nieta = self.log(self.grandchild, old=3, new=1)
        copia_nieta = self.root_copy(en_nieta)
        en_raiz = self.log(self.root, old=1, new=0)
        copias = migration.find_root_copies(ObjectLogChange, OrganizationStructure)
        self.assertEqual(copias, {copia_hija.pk, copia_nieta.pk})
        self.assertNotIn(en_raiz.pk, copias)

    def test_misma_accion_repetida_en_la_raiz_no_es_copia(self):
        self.log(self.root)
        self.log(self.root)
        self.assertEqual(migration.find_root_copies(ObjectLogChange, OrganizationStructure), set())

    def test_filtro_del_admin_incluye_organizaciones_hijas(self):
        en_hija = self.log(self.child)
        en_nieta = self.log(self.grandchild, old=3, new=1)
        en_raiz = self.log(self.root, old=1, new=0)
        model_admin = site._registry[ObjectLogChange]
        request = RequestFactory().get("/")

        def filtrar(organization):
            filtro = OrganizationWithChildrenFilter(
                request, {"organization_tree": [str(organization.pk)]}, ObjectLogChange, model_admin
            )
            return set(filtro.queryset(request, ObjectLogChange.objects.all()).values_list("pk", flat=True))

        self.assertEqual(filtrar(self.root), {en_hija.pk, en_nieta.pk, en_raiz.pk})
        self.assertEqual(filtrar(self.child), {en_hija.pk, en_nieta.pk})
