from django.test import TestCase

from laboratory.test.utils import OrganizationalStructureDataMixin as OrganizationalStructureData


class ShelfViewTestCases(TestCase):

    def setUp(self):
        infrastructure = OrganizationalStructureData()
        infrastructure.setUp()