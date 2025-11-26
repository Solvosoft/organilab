import json

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import NotFound

from academic.models import MyProcedure, ProcedureStep, CommentProcedureStep
from laboratory.models import OrganizationStructure, Laboratory


class MyProceduresViewTest(TestCase):
    fixtures = ["my_procedure.json"]

    def setUp(self):
        self.client = Client()
        self.first_user = User.objects.get(pk=1)
        self.external_user = User.objects.get(pk=3)
        self.organization = OrganizationStructure.objects.get(pk=1)
        self.lab = Laboratory.objects.get(pk=1)

    def test_get_my_procedures_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.external_user)
        url = reverse(
            "academic:get_my_procedures",
            kwargs={"org_pk": self.organization.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_my_procedures_forbidden_for_non_organization_member_users(self):
        self.client.force_login(self.external_user)
        url = reverse(
            "academic:add_my_procedures",
            kwargs={
                "content_type": "laboratory",
                "model": "laboratory",
                "lab_pk": self.lab.pk,
                "org_pk": self.organization.pk,
            },
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_my_procedures_forbidden_for_non_organization_member_users(self):
        my_procedure = MyProcedure.objects.get(pk=1)
        self.client.force_login(self.external_user)
        url = reverse(
            "academic:remove_my_procedure",
            kwargs={
                "lab_pk": self.lab.pk,
                "org_pk": self.organization.pk,
                "pk": my_procedure.pk,
            },
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_page_redirects_for_non_logged_in_user(self):
        url = reverse(
            "academic:get_my_procedures",
            kwargs={"org_pk": self.organization.pk, "lab_pk": self.lab.pk},
        )
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, "/accounts/login/?next=" + url)

    def test_update_my_procedure(self):
        my_procedure = MyProcedure.objects.get(pk=1)
        self.client.force_login(self.first_user)
        url = reverse(
            "academic:complete_my_procedure",
            kwargs={
                "org_pk": self.organization.pk,
                "lab_pk": self.lab.pk,
                "pk": my_procedure.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {"csrfmiddlewaretoken": "", "status": "Finalized"}

        self.client.post(url, data=data)
        self.assertEqual(data["status"], MyProcedure.objects.get(pk=1).status)

    def test_create_my_procedure(self):
        data = {"name": "Second my procedure", "custom_procedure": 10}
        self.client.force_login(self.first_user)
        url = reverse(
            "academic:add_my_procedures",
            kwargs={
                "org_pk": self.organization.pk,
                "lab_pk": self.lab.pk,
                "content_type": "laboratory",
                "model": "laboratory",
            },
        )
        response = self.client.post(url, data=data)
        success_url = reverse(
            "academic:get_my_procedures",
            kwargs={"org_pk": self.organization.pk, "lab_pk": self.lab.pk},
        )
        self.assertRedirects(response, success_url)
        self.assertIn(
            "Second my procedure",
            list(MyProcedure.objects.values_list("name", flat=True)),
        )

    def test_delete_my_procedure(self):
        my_procedure = MyProcedure.objects.get(name="First my procedure test")
        self.client.force_login(self.first_user)
        url = reverse(
            "academic:remove_my_procedure",
            kwargs={
                "org_pk": self.organization.pk,
                "lab_pk": self.lab.pk,
                "pk": my_procedure.pk,
            },
        )
        response = self.client.post(url, follow=True)
        success_url = reverse(
            "academic:get_my_procedures",
            kwargs={"org_pk": self.organization.pk, "lab_pk": self.lab.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertRedirects(response, success_url)
        self.assertNotIn(
            "First my procedure test",
            list(MyProcedure.objects.values_list("name", flat=True)),
        )


class CompleteMyProcedureViewTest(TestCase):
    fixtures = ["object.json", "my_procedure.json"]

    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()
        self.first_user = User.objects.get(pk=1)
        self.external_user = User.objects.get(pk=3)
        self.organization = OrganizationStructure.objects.get(pk=1)
        self.lab = Laboratory.objects.get(pk=1)

    def test_complete_my_procedure_forbidden_for_non_organization_member_users(self):
        my_procedure = MyProcedure.objects.get(pk=1)
        self.client.force_login(self.external_user)
        url = reverse(
            "academic:complete_my_procedure",
            kwargs={
                "lab_pk": self.lab.pk,
                "org_pk": self.organization.pk,
                "pk": my_procedure.pk,
            },
        )
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_query_if_not_logged_in(self):
        response = self.api_client.get(
            reverse(
                "laboratory:api-my-procedure-list-comments",
                kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
            )
            + "?format=datatables"
        )
        result = response.json()
        expected = NotFound.default_detail
        self.assertFalse("recordsTotal" in result)
        self.assertEqual(result["detail"], expected)

    def test_comments_list_without_specified_step(self):
        self.client.force_login(self.first_user)
        search_script = (
            "?offset=0&limit=10&draw=7&ordering=created_by"
            "&my_procedure=1&_=1685373101914"
        )
        url = (
            reverse(
                "laboratory:api-procedure-comments-list",
                kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
            )
            + search_script
        )
        response = self.client.get(url)
        expected = 4
        result = response.json()
        self.assertEqual(result["recordsFiltered"], expected)

    def test_comments_list_by_procedure_step(self):
        step = ProcedureStep.objects.get(pk=17)
        data = {
            "procedure_step": step.pk,
        }
        self.client.force_login(self.first_user)
        url = reverse(
            "laboratory:api-my-procedure-list-comments",
            kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
        )
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("First test comment", json.loads(response.content)["data"])

    def test_add_comment_to_step(self):
        step = ProcedureStep.objects.get(pk=24)
        my_procedure = MyProcedure.objects.get(pk=1)
        data = {
            "procedure_step": step.pk,
            "my_procedure": my_procedure.pk,
            "comment": "This is a comment",
        }
        self.client.force_login(self.first_user)
        url = reverse(
            "laboratory:api-my-procedure-add-comment",
            kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
        )
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(data["comment"], json.loads(response.content)["data"])

    def test_get_comment(self):
        comment = CommentProcedureStep.objects.first()
        self.client.force_login(self.first_user)
        url = reverse(
            "laboratory:api-my-procedure-detail",
            kwargs={
                "lab_pk": self.lab.pk,
                "org_pk": self.organization.pk,
                "pk": comment.pk,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(comment.pk, json.loads(response.content)["id"])

    def test_update_comment(self):
        step = ProcedureStep.objects.get(pk=17)
        my_procedure = MyProcedure.objects.get(pk=1)
        comment = CommentProcedureStep.objects.filter(
            procedure_step=step, my_procedure=my_procedure
        ).first()
        data = {"comment": "Updating comment"}
        self.client.force_login(self.first_user)
        url = reverse(
            "laboratory:api-my-procedure-update-comment",
            kwargs={
                "lab_pk": self.lab.pk,
                "org_pk": self.organization.pk,
                "pk": comment.pk,
            },
        )
        response = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refresh comment values
        comment = CommentProcedureStep.objects.filter(
            procedure_step=step, my_procedure=my_procedure
        ).first()
        self.assertEqual(comment.comment, data["comment"])

    def test_delete_comment(self):
        step = ProcedureStep.objects.get(pk=17)
        my_procedure = MyProcedure.objects.get(pk=1)
        comments_list = CommentProcedureStep.objects.filter(
            procedure_step=step, my_procedure=my_procedure
        )
        total_comment = comments_list.count()
        comment = comments_list.last()
        self.client.force_login(self.first_user)
        url = reverse(
            "laboratory:api-my-procedure-delete-comment",
            kwargs={
                "lab_pk": self.lab.pk,
                "org_pk": self.organization.pk,
                "pk": comment.pk,
            },
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refresh comments list
        comments_list = CommentProcedureStep.objects.filter(
            procedure_step=step, my_procedure=my_procedure
        )
        self.assertEqual(total_comment - 1, comments_list.count())

    def test_general_filter_input_returns_one_record(self):
        self.client.force_login(self.first_user)
        search_script = (
            "?offset=0&limit=10&draw=7&search=test&ordering="
            "created_by&procedure_step=24&my_procedure=1&_=1685373101914"
        )
        url = (
            reverse(
                "laboratory:api-procedure-comments-list",
                kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
            )
            + search_script
        )
        response = self.client.get(url)
        expected = 1
        result = response.json()
        self.assertEqual(result["recordsFiltered"], expected)

    def test_created_by_filter_input_returns_one_record(self):
        self.client.force_login(self.first_user)
        search_script = (
            "?offset=0&limit=10&draw=13&created_by=seco&created_by__"
            "icontains=seco&ordering=created_by&procedure_step=24&my_procedure=1&_=1685373101920"
        )
        url = (
            reverse(
                "laboratory:api-procedure-comments-list",
                kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
            )
            + search_script
        )
        response = self.client.get(url)
        expected = 1
        result = response.json()
        self.assertEqual(result["recordsFiltered"], expected)

    def test_creation_date_filter_input_returns_one_record(self):
        self.client.force_login(self.first_user)
        search_script = (
            "?offset=0&limit=10&draw=2&created_by_at=05%2F14%2F2023%2000%3A00%20AM%20-"
            "%2005%2F16%2F2023%2023%3A59%20PM&ordering=created_by&procedure_step=17&"
            "my_procedure=1&_=1685392101339"
        )
        url = (
            reverse(
                "laboratory:api-procedure-comments-list",
                kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
            )
            + search_script
        )
        response = self.client.get(url)
        expected = 2
        result = response.json()
        self.assertEqual(result["recordsFiltered"], expected)

    def test_comment_filter_input_returns_one_record(self):
        self.client.force_login(self.first_user)
        search_script = (
            "?offset=0&limit=10&draw=28&comment=Standard%20comment&comment__icontains=Standard%20comment"
            "&ordering=created_by&procedure_step=17&my_procedure=1&_=1685392745477"
        )
        url = (
            reverse(
                "laboratory:api-procedure-comments-list",
                kwargs={"lab_pk": self.lab.pk, "org_pk": self.organization.pk},
            )
            + search_script
        )
        response = self.client.get(url)
        expected = 1
        result = response.json()
        self.assertEqual(result["recordsFiltered"], expected)
