from laboratory.tests.gtapi.base import ShelfViewTestOrgCanManageLab, ShelfViewTestOrgCannotManageLab

class ShelfViewTest1(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_shelf_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_shelf_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_shelf_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_shelf_by_shelfobject(self.user4, self.client4)

class ShelfViewTest2(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_shelf_by_shelfobject(user_access=True)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_shelf_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_shelf_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_shelf_by_shelfobject(self.user4, self.client4)

class ShelfViewTest3(ShelfViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without related furniture(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_shelf_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_shelf_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_shelf_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_shelf_by_shelfobject(self.user4, self.client4)

class ShelfViewTest4(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * With required data
    """

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_shelf_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_shelf_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_shelf_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_shelf_by_shelfobject(self.user4, self.client4)

class ShelfViewTest5(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_shelf_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_shelf_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_shelf_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_shelf_by_shelfobject(self.user4, self.client4)

class ShelfViewTest6(ShelfViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without related furniture(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_shelf_by_shelfobject_case1(self):
        self.get_shelf_by_shelfobject()

    def test_get_shelf_by_shelfobject_case2(self):
        self.get_shelf_by_shelfobject(self.user2, self.client2)

    def test_get_shelf_by_shelfobject_case3(self):
        self.get_shelf_by_shelfobject(self.user3, self.client3)

    def test_get_shelf_by_shelfobject_case4(self):
        self.get_shelf_by_shelfobject(self.user4, self.client4)
