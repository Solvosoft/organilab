from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.utils.timezone import now

from academic.models import Procedure, ProcedureRequiredObject
from laboratory.models import ShelfObject
from laboratory.tests.utils import ShelfObjectSetUp
from laboratory.utils import check_user_access_kwargs_org_lab
from reservations_management.models import ReservedProducts, SELECTED
import json
from django.utils.translation import gettext_lazy as _

class ShelfObjectReserveByLabViewTest(ShelfObjectSetUp):
    """
    *** Reserve shelf object by laboratory view ***
    This test does reserve shelfobject request by post method and action 'reserve'
        located in laboratory/api/shelfobject.py --> ShelfObjectViewSet generic view set class.
    """

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.lab = self.lab1_org1
        self.user = self.user1_org1
        self.client = self.client1_org1
        self.shelf_object = ShelfObject.objects.get(pk=1)
        self.initial_date = now() + relativedelta(days=+100)
        self.final_date = now() + relativedelta(days=+200)
        self.data = {
            "amount_required": 2,
            "initial_date": self.initial_date.strftime("%Y-%m-%d %H:%M"),
            "final_date": self.final_date.strftime("%Y-%m-%d %H:%M"),
            "shelf_object": self.shelf_object.pk
        }
        self.filters = {
            "initial_date__date": self.initial_date.date(),
            "final_date__date": self.final_date.date(),
            "amount_required": self.data['amount_required'],
            "shelf_object": self.data['shelf_object'],
            "status": SELECTED,
            "user": self.user
        }

        self.url = reverse("laboratory:api-shelfobject-reserve",
                           kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def test_shelfobject_reserve_by_labview_case1(self):
        """
        #EXPECTED CASE(User 1 in this organization with permissions try to reserve shelfobject)

        CHECK TESTS
        1) Check response status code equal to 200.
        2) Check if user has permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if reserved product instance was created.
        """
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertEqual(self.shelf_object.shelf.furniture.labroom.laboratory.pk,
                         self.lab.pk)

        reserved_products = ReservedProducts.objects.filter(**self.filters).distinct()
        self.assertTrue(reserved_products.exists())

    def test_shelfobject_reserve_by_labview_case2(self):
        """
        #UNEXPECTED CASE, BUT POSSIBLE(User 2 to other organization without permissions try to reserve shelfobject)

        CHECK TESTS
        1) Check response status code equal to 403.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if pk laboratory related to this shelfobject is equal to declared pk laboratory in url.
        4) Check if reserved product instance wasn't created.
        """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertEqual(self.shelf_object.shelf.furniture.labroom.laboratory.pk,
                         self.lab.pk)

        self.filters.update({"user": self.user})
        reserved_products = ReservedProducts.objects.filter(**self.filters).distinct()
        self.assertFalse(reserved_products.exists())


class ShelfObjectReserveByProcedureViewTest(ShelfObjectSetUp):
    """
    *** Reserve shelf object by procedure ***
    This test does reserve shelfobject request by post method located in
     academic/views.py -->  generate_reservation function.
    """

    def setUp(self):
        super().setUp()
        self.org = self.org1
        self.lab = self.lab1_org1
        self.user = self.user1_org1
        self.client = self.client1_org1
        self.initial_date = now() + relativedelta(days=+50)
        self.final_date = now() + relativedelta(days=+100)
        self.procedure = Procedure.objects.get(pk=1)
        self.data = {
            'procedure': self.procedure.pk,
            'initial_date': self.initial_date.strftime("%Y-%m-%d %H:%M"),
            'final_date': self.final_date.strftime("%Y-%m-%d %H:%M")
        }
        self.objects_list = ProcedureRequiredObject.objects. \
            filter(step__procedure__pk=self.data['procedure']). \
            values_list('object', flat=True)
        self.filters = {
            "initial_date__date": self.initial_date.date(),
            "final_date__date": self.final_date.date(),
            "status": SELECTED,
            "user": self.user,
            "laboratory": self.lab,
            "organization": self.org
        }
        self.url = reverse("academic:generate_reservation",
                           kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})

    def validate_reservation_dates(self, initial_date, final_date):
        dates_errors = []
        current_date = now().date()

        if initial_date == final_date:
            dates_errors.append(_("Final date can't be equal to initial date"))
        if initial_date >= final_date:
            dates_errors.append(_("Initial date can't be greater than final date"))
        elif initial_date <= current_date:
            dates_errors.append(
                _("Initial date can't be equal or lower to current date"))
        elif initial_date <= current_date:
            dates_errors.append(_("Initial date can't be lower than current date"))
        elif final_date <= current_date:
            dates_errors.append(_("Final date can't be lower than current date"))
        return dates_errors

    def check_status_view(self, response, required_state):
        if response.status_code != 403:
            if response.content:
                response_data = json.loads(response.content)
                if 'state' in response_data:
                    self.assertEqual(required_state, response_data['state'])

    def check_reservedproducts(self, step_objects, required_state):
        for step_obj in step_objects:
            self.filters.update(
                {"shelf_object__object__pk": step_obj.object.pk})
            reserved_products = ReservedProducts.objects.filter(
                **self.filters).distinct()
            self.assertEqual(required_state, reserved_products.exists())

    def test_shelfobject_reserve_by_procedure_case1(self):
        """
       #EXPECTED CASE(User 1 in this organization with permissions try to reserve shelfobject by procedure without objects in its steps)

       CHECK TESTS
       1) Check response status code equal to 400.
       2) Check if user has permission to access this organization and laboratory.
       3) Check if reservation dates are valid.
       4) Check variable state returned by response data.
       5) Check if procedure has objects to reserve.
       6) Check if procedure step has procedure required object related.
       7) Check if reserved product instance was created.
       """
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertFalse(self.validate_reservation_dates(self.initial_date.date(),
                                                         self.final_date.date()))
        self.check_status_view(response, False)
        self.assertFalse(self.objects_list)

        step_objects = ProcedureRequiredObject.objects.filter(
            object__in=self.objects_list)
        self.assertFalse(step_objects.exists())

        self.check_reservedproducts(step_objects, False)

    def test_shelfobject_reserve_by_procedure_case2(self):
        """
       #UNEXPECTED CASE, BUT POSSIBLE(User 2 to other organization without permissions try to reserve shelfobject by procedure)

        CHECK TESTS
        1) Check response status code equal to 302.
        2) Check if user doesn't have permission to access this organization and laboratory.
        3) Check if reservation dates are valid.
        4) Check variable state returned by response data.
        5) Check if procedure has objects to reserve.
        6) Check if procedure step has procedure required object related.
        7) Check if reserved product instance wasn't created.
       """
        self.client = self.client2_org2
        self.user = self.user2_org2
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertFalse(self.validate_reservation_dates(self.initial_date.date(),
                                                         self.final_date.date()))
        self.check_status_view(response, False)
        self.assertFalse(self.objects_list)

        step_objects = ProcedureRequiredObject.objects.filter(
            object__in=self.objects_list)
        self.assertFalse(step_objects.exists())

        self.filters.update({"user": self.user})
        self.check_reservedproducts(step_objects, False)

    def test_shelfobject_reserve_by_procedure_case3(self):
        """
       #UNEXPECTED CASE, BUT POSSIBLE(User 1 in this organization with permissions try to reserve shelfobject by procedure with amount object equal to 0)

       CHECK TESTS
       1) Check response status code equal to 400.
       2) Check if user has permission to access this organization and laboratory.
       3) Check if reservation dates are valid.
       4) Check variable state returned by response data.
       5) Check if procedure steps have objects.
       6) Check if procedure step has procedure required object related.
       7) Check if object quantity is less or equal than zero.
       8) Check if reserved product instance wasn't created.
       """
        self.procedure = Procedure.objects.get(pk=2)
        self.data['procedure'] = self.procedure.pk
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertFalse(self.validate_reservation_dates(self.initial_date.date(),
                                                         self.final_date.date()))
        self.check_status_view(response, False)

        self.objects_list = ProcedureRequiredObject.objects. \
            filter(step__procedure__pk=self.data['procedure']). \
            values_list('object', flat=True)
        self.assertTrue(self.objects_list)

        step_objects = ProcedureRequiredObject.objects.filter(
            object__in=self.objects_list)
        self.assertTrue(step_objects.exists())

        objects_quantity_less_or_equal_zero = step_objects.filter(quantity__lte=0)
        self.assertTrue(objects_quantity_less_or_equal_zero.exists())

        self.check_reservedproducts(step_objects, False)

    def test_shelfobject_reserve_by_procedure_case4(self):
        """
       #EXPECTED CASE(User 1 in this organization with permissions try to reserve shelfobject by procedure with objects in its steps)

       CHECK TESTS
       1) Check response status code equal to 200.
       2) Check if user has permission to access this organization and laboratory.
       3) Check if reservation dates are valid.
       4) Check variable state returned by response data.
       5) Check if procedure has objects to reserve.
       6) Check if procedure step has procedure required object related.
       7) Check if reserved product instance was created.
       """
        self.procedure = Procedure.objects.get(pk=3)
        self.data['procedure'] = self.procedure.pk
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertFalse(self.validate_reservation_dates(self.initial_date.date(),
                                                         self.final_date.date()))
        self.check_status_view(response, True)

        self.objects_list = ProcedureRequiredObject.objects. \
            filter(step__procedure__pk=self.data['procedure']). \
            values_list('object', flat=True)
        self.assertTrue(self.objects_list)

        step_objects = ProcedureRequiredObject.objects.filter(
            object__in=self.objects_list)
        self.assertTrue(step_objects.exists())

        self.check_reservedproducts(step_objects, True)

    def test_shelfobject_reserve_by_procedure_case5(self):
        """
       #UNEXPECTED CASE, BUT POSSIBLE(User 4 to other organization with permissions try to reserve shelfobject by procedure with amount object equal to 0)

       CHECK TESTS
       1) Check response status code equal to 403.
       2) Check if user has permission to access this organization and laboratory.
       3) Check if reservation dates are valid.
       4) Check variable state returned by response data.
       5) Check if procedure steps have objects.
       6) Check if procedure step has procedure required object related.
       7) Check if object quantity is less or equal than zero.
       8) Check if reserved product instance wasn't created.
       """
        self.procedure = Procedure.objects.get(pk=2)
        self.data['procedure'] = self.procedure.pk
        self.client = self.client4_org2
        self.user = self.user4_org2
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertFalse(self.validate_reservation_dates(self.initial_date.date(),
                                                         self.final_date.date()))
        self.check_status_view(response, False)

        self.objects_list = ProcedureRequiredObject.objects. \
            filter(step__procedure__pk=self.data['procedure']). \
            values_list('object', flat=True)
        self.assertTrue(self.objects_list)

        step_objects = ProcedureRequiredObject.objects.filter(
            object__in=self.objects_list)
        self.assertTrue(step_objects.exists())

        objects_quantity_less_or_equal_zero = step_objects.filter(quantity__lte=0)
        self.assertTrue(objects_quantity_less_or_equal_zero.exists())

        self.filters.update({"user": self.user})
        self.check_reservedproducts(step_objects, False)

    def test_shelfobject_reserve_by_procedure_case6(self):
        """
       #EXPECTED CASE(User 1 in this organization with permissions try to reserve shelfobject by procedure with objects in its steps)

       CHECK TESTS
       1) Check response status code equal to 400.
       2) Check if user has permission to access this organization and laboratory.
       3) Check if reservation dates are valid.
       4) Check variable state returned by response data.
       5) Check if procedure has objects to reserve.
       6) Check if procedure step has procedure required object related.
       7) Check if reserved product instance was created.
       """
        self.procedure = Procedure.objects.get(pk=3)
        self.final_date = now() + relativedelta(days=+50)
        self.initial_date = now() + relativedelta(days=+100)
        self.data.update({
            'procedure': self.procedure.pk,
            'initial_date': self.initial_date.strftime("%Y-%m-%d %H:%M"),
            'final_date': self.final_date.strftime("%Y-%m-%d %H:%M")
        })
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            check_user_access_kwargs_org_lab(self.org.pk, self.lab.pk, self.user))
        self.assertTrue(self.validate_reservation_dates(self.initial_date.date(),
                                                        self.final_date.date()))
        self.check_status_view(response, False)

        self.objects_list = ProcedureRequiredObject.objects. \
            filter(step__procedure__pk=self.data['procedure']). \
            values_list('object', flat=True)
        self.assertTrue(self.objects_list)

        step_objects = ProcedureRequiredObject.objects.filter(
            object__in=self.objects_list)
        self.assertTrue(step_objects.exists())

        self.check_reservedproducts(step_objects, False)
