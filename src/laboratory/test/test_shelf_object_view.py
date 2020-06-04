from unittest.case import TestCase

from laboratory.test.utils import OrganizationalStructureDataMixin


class ShelfObjectViewTestCases(TestCase):

    def setUp(self):
        infrastructure = OrganizationalStructureDataMixin()
        infrastructure.setUp()
