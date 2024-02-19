from django.db.models import Value, DateField
from django.urls import reverse
from django.utils.timezone import now
from django.test import RequestFactory
from laboratory.api.serializers import InformSerializer
from laboratory.models import Inform, CommentInform, InformsPeriod
from laboratory.tests.utils import BaseLaboratorySetUpTest
import json


class InformViewTest(BaseLaboratorySetUpTest):

    def test_get_inform_list(self):
        url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        response = self.client.get(url)
        inform_name_list = [inform.name for inform in response.context['informs']]
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gestión de laboratorio', inform_name_list)
        self.assertTrue(response.context['informs'].count() > 0)

    def test_update_inform(self):
        url = reverse("laboratory:complete_inform", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": 1})
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Gestión de laboratorio")

        data = {
            "csrfmiddlewaretoken": "",
            "status": "Finalized"
        }
        self.client.post(url, data=data)
        self.assertEqual(data["status"], Inform.objects.get(pk=1).status)

    def test_create_inform(self):
        data = {
            "name": "Uso de instrumentos de laboratorio",
            "custom_form": 1
        }
        url = reverse("laboratory:add_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk,
                                                        "content_type": "laboratory", "model": "laboratory"})
        response = self.client.post(url, data=data)
        success_url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertRedirects(response, success_url)
        self.assertIn("Uso de instrumentos de laboratorio", list(Inform.objects.values_list("name", flat=True)))

    def test_delete_inform(self):
        inform = Inform.objects.get(name="Reactivos mensuales despachados")
        url = reverse("laboratory:remove_inform", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk, "pk": inform.pk})
        response = self.client.post(url, follow=True)
        success_url = reverse("laboratory:get_informs", kwargs={"org_pk": self.org.pk, "lab_pk": self.lab.pk})
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, success_url)
        self.assertNotIn("Reactivos mensuales despachados", list(Inform.objects.values_list("name", flat=True)))

    def test_api_informs_detail(self):

        period = InformsPeriod.objects.first()
        inform_list = period.informs.all()
        url = reverse("laboratory:api-informs-detail", kwargs={"pk": self.org.pk})
        data = {
            'period': period.pk
        }
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        content_obj = json.loads(response.content)
        self.assertContains(response, '<a href=\\"/lab/1/1/informs/complete_inform/1/\\">')
        self.assertEqual(content_obj['recordsFiltered'], inform_list.count())

class CommentInformViewTest(BaseLaboratorySetUpTest):

    def test_comment_list_by_inform(self):
        inform = Inform.objects.first()
        data = {
            "inform": inform.pk,
        }
        url = reverse("laboratory:api-inform-list", kwargs={"org_pk":self.org.pk})
        response = self.client.get(url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Describir porque sucedieron los hechos.", json.loads(response.content)['data'])

    def test_add_comment_to_inform(self):
        inform = Inform.objects.last()
        data = {
            "inform": inform.pk,
            "comment": "Revisar fecha de ingreso y salida del informe #"+ str(inform.pk)
        }
        url = reverse("laboratory:api-inform-list", kwargs={"org_pk":self.org.pk})
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn(data['comment'], json.loads(response.content)['data'])

    def test_get_comment(self):
        comment = CommentInform.objects.first()
        url = reverse("laboratory:api-inform-detail", kwargs={"pk": comment.pk,"org_pk":self.org.pk })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content_obj = json.loads(response.content)
        self.assertEqual(content_obj['id'], comment.pk)

    def test_update_comment(self):
        inform = Inform.objects.first()
        comment = CommentInform.objects.filter(inform=inform).last()
        data = {"comment": "Llenar todos los campos del informe."}
        url = reverse("laboratory:api-inform-detail", kwargs={"pk": comment.pk, "org_pk":self.org.pk })
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        #Refresh variable commment
        comment = CommentInform.objects.filter(inform=inform).last()
        self.assertEqual(comment.comment, data['comment'])

    def test_delete_comment(self):
        inform = Inform.objects.last()
        comment_list = CommentInform.objects.filter(inform=inform)
        total_comment = comment_list.count()
        comment = comment_list.last()
        url = reverse("laboratory:api-inform-detail", kwargs={"pk": comment.pk, "org_pk": self.org.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        #Refresh variable commment_list
        comment_list = CommentInform.objects.filter(inform=inform)
        self.assertEqual(total_comment-1, comment_list.count())

class InformSchedulerViewTest(BaseLaboratorySetUpTest):

    def test_inform_index(self):
        url = reverse("laboratory:inform_index", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_add_period_scheduler(self):
        url = reverse("laboratory:add_period_scheduler", kwargs={"org_pk": self.org.pk, })
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_period_scheduler(self):
        url = reverse("laboratory:edit_period_scheduler", kwargs={"org_pk": self.org.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_period_scheduler(self):
        url = reverse("laboratory:detail_period_scheduler", kwargs={"org_pk": self.org.pk, "pk": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
