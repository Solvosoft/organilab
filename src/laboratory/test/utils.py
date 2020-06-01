
from laboratory.models import OrganizationStructure, Laboratory
from django.contrib.auth.models import User, Group
from django.test import RequestFactory
from constance import config


class OrganizationalStructureDataMixin(object):
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

    USER_ADMIN = "user_admin"
    USER_LABORATORIST = "user_laboratorist"
    USER_STUDENT = "user_student"
    PASSWORD = "abcd"

    def setUp(self):
        self.root_organization = OrganizationStructure.objects.create(
            name="the university",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK)
        )
        self.dep1 = OrganizationStructure.objects.create(
            name="departament 1",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.root_organization
        )
        self.dep2 = OrganizationStructure.objects.create(
            name="departament 2",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.root_organization
        )

        self.dep3 = OrganizationStructure.objects.create(
            name="departament 3",
            group=Group.objects.get(pk=config.GROUP_ADMIN_PK),
            parent=self.root_organization
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

        ################################################################################################################
        self.user_admin = User.objects.create_user(
            self.USER_ADMIN,
            "admin@organillab.org",
            self.PASSWORD
        )
        self.user_laboratoris = User.objects.create_user(
            self.USER_LABORATORIST,
            "laboratoris@organillab.org",
            self.PASSWORD
        )
        self.user_student = User.objects.create_user(
            self.USER_STUDENT,
            "student@organillab.org",
            self.PASSWORD
        )

        admin_group = Group.objects.get(pk=config.GROUP_ADMIN_PK)
        laboratoris_group = Group.objects.get(pk=config.GROUP_LABORATORIST_PK)
        student_group = Group.objects.get(pk=config.GROUP_STUDENT_PK)

        self.user_admin.groups.add(admin_group)
        self.user_laboratoris.groups.add(laboratoris_group)
        self.user_student.groups.add(student_group)

        self.factory = RequestFactory()

        pt = PrincipalTechnician(name=self.user_admin.first_name + " " + self.user_admin.last_name,
                                 phone_number="8888-8888",
                                 id_card="0-0000-0000",
                                 email=self.user_admin.email,
                                 organization=self.root_organization
                                 )

        pt.save()
        pt.credentials.add(self.user_admin)
        self.user_admin.groups.add(admin_group)
        self.user_admin.save()


"""
    Laboratory Administrator's group (GROUP_ADMIN_PK) have some permissions like:

    perms_laboratory = [  
         # reservations
        "add_reservation", "change_reservation", "delete_reservation", "add_reservationtoken",
        "change_reservationtoken", "delete_reservationtoken", "view_reservation",

        # shelf
        "view_shelf", "add_shelf", "change_shelf", "delete_shelf",

        # shelfobjets
        "view_shelfobject", "add_shelfobject", "change_shelfobject", "delete_shelfobject",

        # objets
        "view_object", "add_object", "change_object", "delete_object",

        # objectfeatures
        "view_objectfeatures", "add_objectfeatures", "change_objectfeatures", "delete_objectfeatures",

        # procedurerequiredobject
        "view_procedurerequiredobject", "add_procedurerequiredobject", "change_procedurerequiredobject",
        "delete_procedurerequiredobject",

        # laboratory
        "view_laboratory", "add_laboratory", "change_laboratory", "delete_laboratory",

        # laboratoryroom
        "view_laboratoryroom", "add_laboratoryroom", "change_laboratoryroom", "delete_laboratoryroom",

        # furniture
        "view_furniture", "add_furniture", "change_furniture", "delete_furniture",

        # Products
        "view_product", "add_product", "change_product", "delete_product",
        # onsertation
        "view_observation", "add_observation", "change_observation", "delete_observation",
        # CL Inventory
        "view_clinventory", "add_clinventory", "change_clinventory", "delete_clinventory", "add_solution",
        # solutions
        "view_solution", "add_solution", "change_solution", "delete_solution",

        # reports
        "view_report", "do_report",
    ]
"""
