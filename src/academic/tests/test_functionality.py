from django.test import TestCase, Client
from django.urls import reverse

from django.contrib.auth.models import User

from laboratory.models import OrganizationStructure, Laboratory


class AcademicTest(TestCase):
    fixtures = ["initialdata.json"]
    def setUp(self):
        self.client = Client()
        #self.create_users()
        #self.create_organization()
        #self.create_labs()

    def test_users(self):
        print(User.objects.all())

    """def test_create_procedure(self):
        x=self.client.login(username='Jose',password='zzz12569')
        print(x)
        response = self.client.post(reverse('academic:procedure_create',kwargs={'lab_pk':1, 'org_pk':2}), {'title':'Noe', 'description':'El mar rojo'})
        print(response.status_code)
        self.assertEqual(response.status_code,200)
        """


    def create_users(self):
        self.user_one= User.objects.create_user(username="Jose",
                                               email="j@gmail.com",
                                               password="zzz12569",
                                                )
        self.user_two= User.objects.create_user(username="Carr",
                                               email="car@gmail.com",
                                               password="zzz12569",
                                                )
        self.user_three= User.objects.create_user(username="María",
                                               email="m@gmail.com",
                                               password="zzz12569",
                                                )

    def create_organization(self):

        self.org_one = OrganizationStructure.objects.create(
            name="Example 1",
            position=2
        )
        self.org_two = OrganizationStructure.objects.create(
            name="Example 2",
            position=1
        )
        self.org_three = OrganizationStructure.objects.create(
            name="Example 3",
            position=1
        )

    def create_labs(self):

        self.lab1 = Laboratory.objects.create(
            name="Laboratory 1",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.org_one
        )
        self.lab2 = Laboratory.objects.create(
            name="Laboratory 2",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.org_one
        )
        self.lab3 = Laboratory.objects.create(
            name="Laboratory 3",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.org_two
        )
        self.lab4 = Laboratory.objects.create(
            name="Laboratory 4",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.org_two
        )
        self.lab5 = Laboratory.objects.create(
            name="Laboratory 5",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.org_three
        )
        self.lab6 = Laboratory.objects.create(
            name="Laboratory 6",
            phone_number="88-0001-7890",
            location="N/D",
            geolocation='9.895804362670006,-84.1552734375',
            organization=self.org_three
        )