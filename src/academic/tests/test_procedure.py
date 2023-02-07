from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from academic.models import Procedure, ProcedureStep, ProcedureObservations
import json

class AcademicTest(TestCase):
    fixtures = ["object.json","procedure.json"]

    def setUp(self):
        self.client = Client()
        self.user = User.objects.get(pk=1)
        self.url_attr= {'lab_pk':1, 'org_pk':2}
        self.procedure = Procedure.objects.get(pk=10)
        self.client.force_login(self.user)


    def test_create_procedure(self):

        data ={
            'title': 'Noe',
            'description': 'El mar rojo'
        }
        response = self.client.post(reverse('academic:procedure_create',kwargs=self.url_attr),data,follow=True)

        self.assertEqual(Procedure.objects.all().count(),2)
        self.assertEqual(response.status_code,200)
        self.assertRedirects(response, reverse('academic:procedure_list', kwargs=self.url_attr))

    def test_update_procedure_get(self):

        data ={
            'title': self.procedure.title,
            'description': 'El mar rojo'
        }

        url = self.url_attr.copy()
        url['pk'] = self.procedure.pk
        response = self.client.get(reverse('academic:procedure_update',kwargs=url),data,follow=True)

        self.assertTemplateUsed(response,template_name="academic/procedure_create.html")


    def test_update_procedure(self):

        data ={
            'title': self.procedure.title,
            'description': 'El mar rojo'
        }

        url = self.url_attr.copy()
        url['pk'] = self.procedure.pk
        response = self.client.post(reverse('academic:procedure_update',kwargs=url),data,follow=True)
        procedure = Procedure.objects.all().first()

        self.assertEqual(data['description'],procedure.description)
        self.assertNotEquals(data['description'],self.procedure.description)
        self.assertEqual(response.status_code,200)
        self.assertRedirects(response, reverse('academic:procedure_list', kwargs=self.url_attr))

    def test_detail_procedure(self):

        url = self.url_attr
        url['pk'] = self.procedure.pk
        response = self.client.get(reverse('academic:procedure_detail',kwargs=url))
        self.assertEqual(response.status_code,200)

    def test_detail_procedure_fail(self):

        url = self.url_attr
        url['pk'] = 0
        response = self.client.get(reverse('academic:procedure_detail',kwargs=url))

        self.assertNotEquals(response.context['procedure'], self.procedure.pk)

        self.assertEqual(response.status_code,200)

    def test_list_procedure(self):

        redirect = self.client.get(reverse('academic:procedure_list', kwargs=self.url_attr), follow=True)

        """This is the default template_name of Procedure ListView"""
        self.assertTemplateUsed(redirect,template_name='academic/procedure_list.html')

        """This is the template_name put in the Procedure ListView"""
        self.assertTemplateNotUsed(redirect,template_name='academic/list.html')
        self.assertEqual(redirect.status_code,200)

    def test_delete_procedure(self):
        data = {
            'pk':self.procedure.pk
        }
        pre_procedures= Procedure.objects.all().count()
        response = self.client.post(reverse('academic:delete_procedure', kwargs=self.url_attr),data)
        pos_procedures= Procedure.objects.all().count()

        self.assertEqual(json.loads(response.content)['data'],True)
        self.assertTrue(pre_procedures>pos_procedures)
        self.assertEqual(response.status_code,200)

    def test_delete_procedure_fail(self):
        data = {
            'pk':0
        }

        pre_procedures= Procedure.objects.all().count()
        response = self.client.post(reverse('academic:delete_procedure', kwargs=self.url_attr),data)
        pos_procedures= Procedure.objects.all().count()

        self.assertEquals(pre_procedures,pos_procedures)
        self.assertEqual(response.status_code,404)

    def test_get_ajax_procedure(self):
        data = {
            'pk':self.procedure.pk
        }
        result = {'title':self.procedure.title,'pk':self.procedure.pk}
        response = self.client.post(reverse('academic:get_procedure', kwargs=self.url_attr),data)

        self.assertEqual(json.loads(response.content)['data'],result)
        self.assertEqual(response.status_code,200)

    def test_get_ajax_procedure_fail(self):
        data = {
            'pk':20
        }

        response = self.client.post(reverse('academic:get_procedure', kwargs=self.url_attr),data)

        self.assertEqual(response.status_code,404)

    def test_add_step_procedure(self):
        url = self.url_attr.copy()
        url['pk']=self.procedure.pk
        early_step = ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')

        response = self.client.post(reverse('academic:add_steps_wrapper', kwargs=url), follow=True)
        step=ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')
        self.assertEqual(response.status_code,200)
        self.assertEqual(step.__str__(),'Paso sin título')
        self.assertNotEquals(step.pk, early_step.pk)

    def test_add_step(self):
        url = self.url_attr.copy()
        url['pk']=self.procedure.pk
        early_step = ProcedureStep.objects.filter(procedure=self.procedure).count()
        data = {
            'title':'Step 1',
            'description':'Testing to add step'
        }

        response = self.client.post(reverse('academic:procedure_step', kwargs=url),data=data, follow=True)
        steps=ProcedureStep.objects.filter(procedure=self.procedure)

        self.assertNotEquals(early_step,steps.count())
        self.assertEqual(response.status_code,200)

    def test_add_step_fail(self):
        self.client.force_login(self.user)
        url = self.url_attr.copy()
        url['pk']=0

        data = {
            'title':'Step 1',
            'description':'Testing to add step'
        }

        response = self.client.post(reverse('academic:procedure_step', kwargs=url),data=data, follow=True)

        self.assertEqual(response.status_code,404)

    def test_update_step(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')
        url['pk']=step.pk
        data = {
            'title':'Step 1',
            'description':'Change description'
        }

        response = self.client.post(reverse('academic:update_step', kwargs=url),data=data, follow=True)
        new_step=ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')

        self.assertNotEquals(step.description,new_step.description)
        self.assertEqual(response.status_code,200)

    def test_update_step_fail(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')
        url['pk']=step.pk
        step.delete()

        response = self.client.get(reverse('academic:update_step', kwargs=url), follow=True)
        self.assertEqual(response.status_code, 404)

    def test_delete_step(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')
        data ={
            'pk':step.pk
        }
        response = self.client.post(reverse('academic:delete_step', kwargs=url),data, follow=True)
        step = ProcedureStep.objects.filter(pk=data['pk']).first()

        self.assertEqual(step, None)
        self.assertEqual(response.status_code, 200)

    def test_add_step_observation(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.filter(procedure=self.procedure).latest('pk')
        url['pk'] = step.pk

        data = {
            'description':'First observation'
        }
        response = self.client.post(reverse('academic:add_observation', kwargs=url),data=data, follow=True)
        obs=ProcedureObservations.objects.filter(step=step)

        self.assertTrue(obs.count()==1)
        self.assertEqual(response.status_code,200)

    def test_delete_procedureobservation(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        obs = ProcedureObservations.objects.filter(step=step).latest('pk')
        url['pk'] = step.pk
        data = {
            'pk':obs.pk
        }

        response = self.client.post(reverse('academic:remove_observation', kwargs=url), data)

        obs=ProcedureObservations.objects.filter(step=step)

        self.assertTrue(obs.count()==1)
        self.assertEqual(json.loads(response.content)['data'], '[{"description": "Cleaning", "id": 1}]')
        self.assertEqual(response.status_code,200)

    def test_delete_procedureobservation_fail(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)

        url['pk'] = step.pk
        data = {
            'pk':80
        }

        response = self.client.post(reverse('academic:remove_observation', kwargs=url), data)

        self.assertEqual(response.status_code,404)

    def test_add_object(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url['pk'] = step.pk
        data = {
               'unit':64,
               'object':75,
               'quantity':8
         }


        response = self.client.post(reverse('academic:add_object', kwargs=url), data)
        self.assertEqual(response.status_code,200)

    def test_remove_object(self):
        url = self.url_attr.copy()
        step = ProcedureStep.objects.get(pk=17)
        url['pk'] = step.pk
        data = {
               'pk':12,
         }


        response = self.client.post(reverse('academic:remove_object', kwargs=url), data)
        self.assertEqual(response.status_code,200)
        self.assertEqual(json.loads(response.content)['data'],'[]')

    def test_procedure_reservation(self):
        from datetime import datetime
        initial_date = datetime(2023, 1, 17, 11, 2, 5)
        final_date = datetime(2023, 1, 22, 11, 2, 5)
        data = {
               'procedure':self.procedure.pk,
               'initial_date':initial_date,
                'final_date': final_date


         }

        response = self.client.post(reverse('academic:generate_reservation', kwargs=self.url_attr), data)
        self.assertEqual(response.status_code,200)
        self.assertEqual(json.loads(response.content)['errors'],'[]')
        self.assertTrue(json.loads(response.content)['state']==True)
