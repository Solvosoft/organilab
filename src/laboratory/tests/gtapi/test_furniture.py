from laboratory.tests.gtapi.base import FurnitureViewTestOrgCanManageLab, FurnitureViewTestOrgCannotManageLab

class FurnitureViewTest1(FurnitureViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * With required data
    """

    def setUp(self):
        super().setUp()

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_furniture_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_furniture_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_furniture_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_furniture_by_shelfobject(self.user4, self.client4)

class FurnitureViewTest2(FurnitureViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_furniture_by_shelfobject(user_access=True)

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_furniture_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_furniture_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_furniture_by_shelfobject(self.user4, self.client4)

class FurnitureViewTest3(FurnitureViewTestOrgCanManageLab):
    """
        * Organization can manage this laboratory
        * Without related labroom(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_furniture_by_shelfobject(user_access=True, status_code=200, results_data=False)

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_furniture_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_furniture_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_furniture_by_shelfobject(self.user4, self.client4)

class FurnitureViewTest4(FurnitureViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * With required data
    """

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_furniture_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_furniture_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_furniture_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_furniture_by_shelfobject(self.user4, self.client4)

class FurnitureViewTest5(FurnitureViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without required data
    """

    def setUp(self):
        super().setUp()
        self.data = {}

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_furniture_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_furniture_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_furniture_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_furniture_by_shelfobject(self.user4, self.client4)

class FurnitureViewTest6(FurnitureViewTestOrgCannotManageLab):
    """
        * Organization cannot manage this laboratory
        * Without related labroom(relfield)
    """

    def setUp(self):
        super().setUp()
        del self.data["relfield"]

    def test_get_furniture_by_shelfobject_case1(self):
        self.get_furniture_by_shelfobject()

    def test_get_furniture_by_shelfobject_case2(self):
        self.get_furniture_by_shelfobject(self.user2, self.client2)

    def test_get_furniture_by_shelfobject_case3(self):
        self.get_furniture_by_shelfobject(self.user3, self.client3)

    def test_get_furniture_by_shelfobject_case4(self):
        self.get_furniture_by_shelfobject(self.user4, self.client4)
