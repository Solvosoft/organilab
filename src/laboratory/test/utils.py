from constance import config
from django.contrib.auth.models import Group

from laboratory.models import OrganizationStructure, Laboratory


class DataMixin(object):
    """
                        -------------------------
                        |          root         |         * = GROUP_STUDENT
                        -------------------------
                        /             |         \
                      dep1           dep2       dep3       GROUP_ADMIN
                   /   \    \      /    \        |  \
                sch1     sch2  sch3    sch4   sch5   sch6  GROUP_LABORATORIST
                /  \      |     |     / |       |      |
              lab1 lab2  lab3  lab4  /isch1    lab8   lab9
                                   lab5 / \
                                     lab6 lab7
    """

    def setUp(self):
        self.root = OrganizationStructure.objects.create(
            name="the university",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK)
        )
        self.dep1 = OrganizationStructure.objects.create(
            name="departament 1",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.root
        )
        self.dep2 = OrganizationStructure.objects.create(
            name="departament 2",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.root
        )

        self.dep3 = OrganizationStructure.objects.create(
            name="departament 3",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.root
        )

        self.school1 = OrganizationStructure.objects.create(
            name="School 1",
            group=Group.objects.get(pk=config.GROUP_LABORATORIST_PK),
            parent=self.dep1
        )
        self.school2 = OrganizationStructure.objects.create(
            name="School 2",
            group=Group.objects.get(pk=config.GROUP_LABORATORIST_PK),
            parent=self.dep1
        )

        self.school3 = OrganizationStructure.objects.create(
            name="School 3",
            group=Group.objects.get(pk=config.GROUP_LABORATORIST_PK),
            parent=self.dep1
        )
        self.school4 = OrganizationStructure.objects.create(
            name="School 4",
            group=Group.objects.get(pk=config.GROUP_STUDENT_PK),
            parent=self.dep2
        )
        self.school5 = OrganizationStructure.objects.create(
            name="School 5",
            group=Group.objects.get(pk=config.GROUP_LABORATORIST_PK),
            parent=self.dep2
        )
        self.school6 = OrganizationStructure.objects.create(
            name="School 6",
            group=Group.objects.get(pk=config.GROUP_LABORATORIST_PK),
            parent=self.dep3
        )
        self.interschool = OrganizationStructure.objects.create(
            name="Inter School 1",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.school4
        )

        """
                      sch1     sch2  sch3    sch4   sch5   sch6   
                      /  \      |     |     / |       |      |
                    lab1 lab2  lab3  lab4  /isch1    lab8   lab9        
                                         lab5 / \ 
                                           lab6 lab7
        """

        self.lab1 = Laboratory.objects.create(
            name="Laboratory 1",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school1
        )
        self.lab2 = Laboratory.objects.create(
            name="Laboratory 2",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school1
        )
        self.lab3 = Laboratory.objects.create(
            name="Laboratory 3",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school2
        )
        self.lab4 = Laboratory.objects.create(
            name="Laboratory 4",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school3
        )
        self.lab5 = Laboratory.objects.create(
            name="Laboratory 5",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school4
        )
        self.lab6 = Laboratory.objects.create(
            name="Laboratory 6",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.interschool
        )
        self.lab7 = Laboratory.objects.create(
            name="Laboratory 7",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.interschool
        )
        self.lab8 = Laboratory.objects.create(
            name="Laboratory 8",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school5
        )
        self.lab9 = Laboratory.objects.create(
            name="Laboratory 9",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.school6
        )



