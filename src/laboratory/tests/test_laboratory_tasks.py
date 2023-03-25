from laboratory.models import Furniture
from laboratory.tasks import remove_shelf_not_furniture
from laboratory.tests.utils import BaseLaboratoryTasksSetUpTest
import re

class RemoveShelfViewTest(BaseLaboratoryTasksSetUpTest):

    def get_remove_shelflist(self):
        shelf_list = []
        furnitures = Furniture.objects.all()
        for furniture in furnitures:
            obj_pks = re.findall(r'\d+', furniture.dataconfig)
            shelf_list = shelf_list + list(furniture.shelf_set.all().exclude(pk__in=obj_pks).values_list('pk', flat=True))
        return shelf_list

    def test_remove_shelf_not_furniture(self):
        shelf_list = self.get_remove_shelflist()
        self.assertEqual(len(shelf_list), 4)
        remove_shelf_not_furniture()
        shelf_list = self.get_remove_shelflist()
        self.assertEqual(len(shelf_list), 0)