import re

from django.urls import reverse
from laboratory.models import Shelf, Furniture
from laboratory.tests.utils import BaseLaboratorySetUpTest
import re


class FurnitureDataconfigTest(BaseLaboratorySetUpTest):

    def test_delete_shelf_in_furniture(self):
        shelf = Shelf.objects.get(pk=4)
        pre_furniture = Furniture.objects.get(shelf=shelf)

        pre_furniture.dataconfig='[[[400],[2],[3],[4]],[[1],[444],[4],[404]]]'
        pre_furniture.save()
        pre_count = pre_furniture.shelf_set.all().count()
        url = reverse("laboratory:shelf_delete", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": shelf.pk,
                                                         "row": shelf.row(), "col": shelf.col()})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        post_furniture = Furniture.objects.get(pk=pre_furniture.pk)
        post_count= post_furniture.shelf_set.all().count()
        shelf_removed = Shelf.objects.filter(pk=4).first()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(post_furniture.dataconfig == '[[[400], [2], [3], []], [[1], [444], [], [404]]]')
        self.assertTrue(pre_count>post_count)
        self.assertIsNone(shelf_removed)


    def test_delete_shelf_in_furniture_col(self):

        pre_furniture = Furniture.objects.get(pk=1)
        pre_furniture.dataconfig = "[[[],[2],[],[3]],[[1],[],[],[4]]]"
        pre_furniture.save()

        data = {
            "name": "Mueble Aéreo",
            "type": 75,
            "labroom": 1,
            "dataconfig": "[[[],[2],[]],[[1],[],[]]]",
            "color": "#73879C",
            "shelfs": '[3,4]'
        }

        url = reverse("laboratory:furniture_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": pre_furniture.pk})
        response = self.client.post(url, data=data)
        shelfs = Shelf.objects.filter(pk__in=re.findall(r'\d+', data['shelfs']))
        post_furniture = Furniture.objects.get(pk=pre_furniture.pk)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(post_furniture.dataconfig == '[[[],[2],[]],[[1],[],[]]]')
        self.assertTrue(shelfs.count() == 0)
        self.assertTrue(post_furniture.shelf_set.all().count()==2)

    def test_delete_shelf_in_furniture_row(self):

        pre_furniture = Furniture.objects.get(pk=1)
        pre_furniture.dataconfig = "[[[],[2],[],[3]],[[1],[],[],[4]]]"
        pre_furniture.save()

        data = {
            "name": "Mueble Aéreo",
            "type": 75,
            "labroom": 1,
            "dataconfig": "[[[],[2],[]]]",
            "color": "#73879C",
            "shelfs": '[1,4]'
        }

        url = reverse("laboratory:furniture_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": pre_furniture.pk})
        response = self.client.post(url, data=data)
        shelfs = Shelf.objects.filter(pk__in=re.findall(r'\d+', data['shelfs']))
        post_furniture = Furniture.objects.get(pk=pre_furniture.pk)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(post_furniture.dataconfig == '[[[],[2],[]]]')
        self.assertTrue(shelfs.count() == 0)
        self.assertTrue(post_furniture.shelf_set.all().count()==2)

    def test_delete_shelf_in_furniture_letter_list(self):

        pre_furniture = Furniture.objects.get(pk=1)
        pre_furniture.dataconfig = "[[[],[2],[],[3]],[[1],[],[],[4]]]"
        pre_furniture.save()

        data = {
            "name": "Mueble Aéreo",
            "type": 75,
            "labroom": 1,
            "dataconfig": "[[[],[2],[],[3]],[[1],[],[],[4]]]",
            "color": "#73879C",
            "shelfs": '[yyu,yi]'
        }

        url = reverse("laboratory:furniture_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": pre_furniture.pk})
        response = self.client.post(url, data=data)
        shelfs = Shelf.objects.filter(pk__in=re.findall(r'\d+', data['shelfs']))
        post_furniture = Furniture.objects.get(pk=pre_furniture.pk)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(shelfs.count() == 0)
        self.assertTrue(post_furniture.shelf_set.all().count()==4)

    def test_delete_shelf_in_furniture_letter(self):

        pre_furniture = Furniture.objects.get(pk=1)
        pre_furniture.dataconfig = "[[[],[2],[],[3]],[[1],[],[],[4]]]"
        pre_furniture.save()

        data = {
            "name": "Mueble Aéreo",
            "type": 75,
            "labroom": 1,
            "dataconfig": "[[[],[2],[],[3]],[[1],[],[],[4]]]",
            "color": "#73879C",
            "shelfs": 'yyu'
        }

        url = reverse("laboratory:furniture_update", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": pre_furniture.pk})
        response = self.client.post(url, data=data)
        shelfs = Shelf.objects.filter(pk__in=re.findall(r'\d+', data['shelfs']))
        post_furniture = Furniture.objects.get(pk=pre_furniture.pk)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(shelfs.count() == 0)
        self.assertTrue(post_furniture.shelf_set.all().count()==4)
