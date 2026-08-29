
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from academic.models import (
    Procedure,
    ProcedureStep,
    ProcedureObservations,
    ProcedureRequiredObject,
)
from derb.models import CustomForm
import json
from datetime import datetime


class AcademicTest(TestCase):
    fixtures = ["object.json", "procedure.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr = {"org_pk": 1}
        self.procedure = Procedure.objects.get(pk=10)
        self.client.force_login(self.user)

    def test_create_procedure(self):

        data = {"title": "Noe", "description": "El mar rojo"}
        response = self.client.post(
            reverse("academic:procedure_create", kwargs=self.url_attr),
            data,
            follow=True,
        )

        self.assertEqual(Procedure.objects.all().count(), 2)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response, reverse("academic:procedure_list", kwargs=self.url_attr)
        )

    def test_update_procedure_get(self):

        data = {"title": self.procedure.title, "description": "El mar rojo"}

        url = self.url_attr.copy()
        url["pk"] = self.procedure.pk
        response = self.client.get(
            reverse("academic:procedure_update", kwargs=url), data, follow=True
        )

        self.assertTemplateUsed(
            response, template_name="academic/procedure_create.html"
        )

    def test_update_procedure(self):

        data = {"title": self.procedure.title, "description": "El mar rojo"}

        url = self.url_attr.copy()
        url["pk"] = self.procedure.pk
        response = self.client.post(
            reverse("academic:procedure_update", kwargs=url), data, follow=True
        )
        procedure = Procedure.objects.all().first()

        self.assertEqual(data["description"], procedure.description)
        self.assertNotEqual(data["description"], self.procedure.description)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(
            response, reverse("academic:procedure_list", kwargs=self.url_attr)
        )

    def test_detail_procedure(self):

        url = self.url_attr
        url["pk"] = self.procedure.pk
        response = self.client.get(reverse("academic:procedure_detail", kwargs=url))
        self.assertEqual(response.status_code, 200)

    def test_detail_procedure_fail(self):

        url = self.url_attr
        url["pk"] = 0
        response = self.client.get(reverse("academic:procedure_detail", kwargs=url))

        self.assertNotEqual(response.context["procedure"], self.procedure.pk)

        self.assertEqual(response.status_code, 200)

    def test_list_procedure(self):

        redirect = self.client.get(
            reverse("academic:procedure_list", kwargs=self.url_attr), follow=True
        )

        """This is the default template_name of Procedure ListView"""
        self.assertTemplateUsed(redirect, template_name="academic/procedure_list.html")

        """This is the template_name put in the Procedure ListView"""
        self.assertTemplateNotUsed(redirect, template_name="academic/list.html")
        self.assertEqual(redirect.status_code, 200)

    def test_delete_procedure(self):
        data = {"pk": self.procedure.pk}
        pre_procedures = Procedure.objects.all().count()
        response = self.client.post(
            reverse("academic:delete_procedure", kwargs=self.url_attr), data
        )
        pos_procedures = Procedure.objects.all().count()

        self.assertEqual(json.loads(response.content)["data"], True)
        self.assertTrue(pre_procedures > pos_procedures)
        self.assertEqual(response.status_code, 200)

    def test_delete_procedure_fail(self):
        data = {"pk": 0}

        pre_procedures = Procedure.objects.all().count()
        response = self.client.post(
            reverse("academic:delete_procedure", kwargs=self.url_attr), data
        )
        pos_procedures = Procedure.objects.all().count()

        self.assertEqual(pre_procedures, pos_procedures)
        self.assertEqual(response.status_code, 302)

    def test_get_ajax_procedure(self):
        self.url_attr["pk"] = self.procedure.pk
        result = {"title": self.procedure.title, "pk": self.procedure.pk}
        response = self.client.get(
            reverse("academic:get_procedure", kwargs=self.url_attr)
        )

        self.assertEqual(json.loads(response.content)["title"], result["title"])
        self.assertEqual(response.status_code, 200)

    def test_get_ajax_procedure_fail(self):
        self.url_attr["pk"] = 20

        response = self.client.get(
            reverse("academic:get_procedure", kwargs=self.url_attr)
        )

        self.assertEqual(response.status_code, 302)

    def test_add_step_procedure(self):
        url = self.url_attr.copy()
        url["pk"] = self.procedure.pk
        early_step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")

        response = self.client.post(
            reverse("academic:add_steps_wrapper", kwargs=url), follow=True
        )
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(step.__str__(), "No titled step")
        self.assertNotEqual(step.pk, early_step.pk)

    def test_add_step(self):
        url = self.url_attr.copy()
        url["pk"] = self.procedure.pk
        early_step = ProcedureStep.objects.filter(procedure=self.procedure).count()
        data = {"title": "Step 1", "description": "Testing to add step"}

        response = self.client.post(
            reverse("academic:procedure_step", kwargs=url), data=data, follow=True
        )
        steps = ProcedureStep.objects.filter(procedure=self.procedure)

        self.assertNotEqual(early_step, steps.count())
        self.assertEqual(response.status_code, 200)

    def test_add_step_fail(self):
        self.client.force_login(self.user)
        url = self.url_attr.copy()
        url["pk"] = 0

        data = {"title": "Step 1", "description": "Testing to add step"}

        response = self.client.post(
            reverse("academic:procedure_step", kwargs=url), data=data, follow=True
        )

        self.assertEqual(response.status_code, 404)

    def test_update_step(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")
        url["pk"] = step.pk
        data = {"title": "Step 1", "description": "Change description"}

        response = self.client.post(
            reverse("academic:update_step", kwargs=url), data=data, follow=True
        )
        new_step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")

        self.assertNotEqual(step.description, new_step.description)
        self.assertEqual(response.status_code, 200)

    def test_update_step_fail(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")
        url["pk"] = step.pk
        step.delete()

        response = self.client.get(
            reverse("academic:update_step", kwargs=url), follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_step(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")
        data = {"pk": step.pk}
        response = self.client.post(
            reverse("academic:delete_step", kwargs=url), data, follow=True
        )
        step = ProcedureStep.objects.filter(pk=data["pk"]).first()

        self.assertEqual(step, None)
        self.assertEqual(response.status_code, 200)

    def test_delete_procedure_observation(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        obs = ProcedureObservations.objects.filter(step=step).latest("pk")
        url["parent_pk"] = step.pk
        url["pk"] = obs.pk

        response = self.client.delete(
            reverse("academic:api-procedureobservation-detail", kwargs=url)
        )

        self.assertEqual(response.status_code, 204)
        self.assertTrue(ProcedureObservations.objects.filter(step=step).count() == 1)

    def test_delete_procedure_observation_fail(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url["parent_pk"] = step.pk
        url["pk"] = 80

        response = self.client.delete(
            reverse("academic:api-procedureobservation-detail", kwargs=url)
        )

        self.assertEqual(response.status_code, 404)

    def test_list_observations(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url["parent_pk"] = step.pk

        response = self.client.get(
            reverse("academic:api-procedureobservation-list", kwargs=url)
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["recordsTotal"], 2)
        self.assertIn("Cleaning", [row["description"] for row in data["data"]])

    def test_add_object(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url["parent_pk"] = step.pk
        data = {"measurement_unit": 64, "object": 75, "quantity": 8}
        total = ProcedureRequiredObject.objects.filter(step=step).count()

        response = self.client.post(
            reverse("academic:api-procedurerequiredobject-list", kwargs=url), data
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            ProcedureRequiredObject.objects.filter(step=step).count(), total + 1
        )

    def test_add_object_invalid_quantity(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url["parent_pk"] = step.pk
        data = {"measurement_unit": 64, "object": 75, "quantity": -5}

        response = self.client.post(
            reverse("academic:api-procedurerequiredobject-list", kwargs=url), data
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.json())

    def test_remove_object(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url["parent_pk"] = step.pk
        url["pk"] = 12

        response = self.client.delete(
            reverse("academic:api-procedurerequiredobject-detail", kwargs=url)
        )

        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProcedureRequiredObject.objects.filter(pk=12).exists())

    def test_remove_object_wrong_parent(self):
        url = self.url_attr.copy()
        other_step = (
            ProcedureStep.objects.filter(procedure=self.procedure)
            .exclude(pk=17)
            .first()
        )
        url["parent_pk"] = other_step.pk
        url["pk"] = 12

        response = self.client.delete(
            reverse("academic:api-procedurerequiredobject-detail", kwargs=url)
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProcedureRequiredObject.objects.filter(pk=12).exists())

    def test_procedure_reservation(self):
        initial_date = datetime(2023, 1, 17, 11, 2, 5)
        final_date = datetime(2023, 1, 22, 11, 2, 5)
        data = {
            "procedure": self.procedure.pk,
            "initial_date": initial_date,
            "final_date": final_date,
        }
        self.url_attr["lab_pk"] = 1
        response = self.client.post(
            reverse("academic:generate_reservation", kwargs=self.url_attr), data
        )
        self.assertEqual(response.status_code, 400)

    def test_add_step_with_form_schema(self):
        url = self.url_attr.copy()
        url["pk"] = self.procedure.pk
        form_schema = json.dumps({
            "display": "form",
            "components": [
                {"type": "textfield", "key": "sample", "label": "Sample", "input": True}
            ],
        })
        data = {
            "title": "Step with form",
            "description": "Step that includes a formio schema",
            "form_schema": form_schema,
        }
        response = self.client.post(
            reverse("academic:procedure_step", kwargs=url), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        step = ProcedureStep.objects.filter(procedure=self.procedure, title="Step with form").first()
        self.assertIsNotNone(step)
        self.assertIsNotNone(step.form)
        self.assertEqual(step.form.schema["components"][0]["key"], "sample")

    def test_update_step_with_form_schema(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")
        url["pk"] = step.pk
        form_schema = json.dumps({
            "display": "form",
            "components": [
                {"type": "textfield", "key": "updated_field", "label": "Updated", "input": True}
            ],
        })
        data = {
            "title": "Step with updated form",
            "description": "Updated description",
            "form_schema": form_schema,
        }
        response = self.client.post(
            reverse("academic:update_step", kwargs=url), data=data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        step.refresh_from_db()
        self.assertIsNotNone(step.form)
        self.assertEqual(step.form.schema["components"][0]["key"], "updated_field")

    def test_update_step_replaces_existing_form_schema(self):
        from laboratory.models import OrganizationStructure
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest("pk")
        org = OrganizationStructure.objects.get(pk=1)
        initial_form = CustomForm.objects.create(
            name="Initial form",
            status="admin",
            schema={"display": "form", "components": [
                {"type": "textfield", "key": "old_field", "label": "Old", "input": True}
            ]},
            organization=org,
        )
        step.form = initial_form
        step.save()

        url["pk"] = step.pk
        new_schema = json.dumps({
            "display": "form",
            "components": [
                {"type": "textfield", "key": "new_field", "label": "New", "input": True}
            ],
        })
        data = {"title": "Step with replaced form", "description": "Description", "form_schema": new_schema}
        self.client.post(reverse("academic:update_step", kwargs=url), data=data, follow=True)

        step.refresh_from_db()
        self.assertIsNotNone(step.form)
        self.assertEqual(step.form.schema["components"][0]["key"], "new_field")
        self.assertEqual(CustomForm.objects.filter(pk=initial_form.pk).first().schema["components"][0]["key"], "new_field")
