# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
'''

from django import forms
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.db.models.query_utils import Q
from django.forms import ModelForm
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import path
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import CustomForm, GTForm
from djgentelella.widgets import core as genwidget

from laboratory.forms import MateriaCapacityObjectForms, ObjectForm
from laboratory.models import Laboratory, BlockedListNotification, \
    OrganizationStructure, MaterialCapacity, Catalog
from laboratory.models import Object, SustanceCharacteristics
from laboratory.utils import filter_laboratorist_profile, organilab_logentry, get_profile_by_organization, \
    get_pk_org_ancestors
from laboratory.views.djgeneric import CreateView, DeleteView, UpdateView, ListView



class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):

        @method_decorator(permission_required('laboratory.add_object'), name='dispatch')
        class ObjectCreateView(CreateView):
            permission_required = ('laboratory.add_object',)

            def get_success_url(self, *args, **kwargs):
                redirect = reverse_lazy('laboratory:objectview_list', args=(
                    self.org, self.lab)) + "?type_id=" + self.object.type
                return redirect

            def get_form_kwargs(self):
                kwargs = super(ObjectCreateView, self).get_form_kwargs()
                kwargs['request'] = self.request
                return kwargs

            def form_valid(self, form):
                object = form.save(commit=False)
                organization = get_object_or_404(OrganizationStructure, pk=self.org)
                object.organization=organization
                changed_data = form.changed_data

                if object.type == Object.MATERIAL:
                    object.save()

                    capacity_data = {'capacity':form.cleaned_data['capacity'],
                                'capacity_measurement_unit': form.cleaned_data['capacity_measurement_unit'].pk,
                                'object':object}

                    capacity_form = MateriaCapacityObjectForms(data=capacity_data)
                    if capacity_form.is_valid():
                        capacity_form.save()

                    changed_data.extend(capacity_form.changed_data)


                organilab_logentry(self.request.user, object, ADDITION, changed_data=changed_data, relobj=self.lab)
                return super(ObjectCreateView, self).form_valid(form)

        self.create = ObjectCreateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html",
        )


        @method_decorator(permission_required('laboratory.change_object'), name='dispatch')
        class ObjectUpdateView(UpdateView):

            def get_success_url(self):
                return reverse_lazy(
                    'laboratory:objectview_list',
                    args=(self.org, self.lab)) + "?type_id=" + self.get_object().type

            def get_form_kwargs(self):
                kwargs = super(ObjectUpdateView, self).get_form_kwargs()
                kwargs['request'] = self.request
                return kwargs

            def form_valid(self, form):
                object = form.save()
                changed_data = form.changed_data

                capacity_form = None
                if object.type==Object.MATERIAL:
                    capacity_data = {'capacity': form.cleaned_data['capacity'],
                                     'capacity_measurement_unit': form.cleaned_data[
                                         'capacity_measurement_unit'].pk,
                                     'object': object}
                    if hasattr(object,'materialcapacity'):
                        capacity_form = MateriaCapacityObjectForms(data=capacity_data, instance=object.materialcapacity)
                    else:
                        capacity_form = MateriaCapacityObjectForms(data=capacity_data)
                    if capacity_form.is_valid():
                        capacity_form.save()
                    changed_data.extend(capacity_form.changed_data)
                organilab_logentry(self.request.user, object, CHANGE,  changed_data=changed_data, relobj=self.lab)
                return super(ObjectUpdateView, self).form_valid(object)

            def form_invalid(self, form):
                response = super().form_invalid(form)
                if self.request.accepts("text/html"):
                    return response
                else:
                    return JsonResponse(form.errors, status=400)

        capacity = None
        self.edit = ObjectUpdateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html"
        )


        @method_decorator(permission_required('laboratory.delete_object'), name='dispatch')
        class ObjectDeleteView(DeleteView):

            def get_success_url(self):
                if 'type_id' in self.request.GET:

                    self.type_id = self.request.GET.get('type_id', '')

                    return reverse_lazy('laboratory:objectview_list',
                                    args=(self.org, self.lab))+"?type_id="+self.type_id
                else:
                    return reverse_lazy('laboratory:objectview_list',
                                    args=(self.org, self.lab))


            def form_valid(self, form):
                success_url = self.get_success_url()
                organilab_logentry(self.request.user, self.object, DELETION, relobj=self.lab)
                self.object.delete()
                return HttpResponseRedirect(success_url)

        self.delete = ObjectDeleteView.as_view(
            model=self.model,
            success_url="/",
            template_name=self.template_name_base + "_delete.html"
        )



        @method_decorator(permission_required('laboratory.view_object'), name='dispatch')
        class ObjectListView(ListView):

            def get_queryset(self):
                query = ListView.get_queryset(self).filter(
                    organization__in=get_pk_org_ancestors(self.org), is_public=True
                )

                if 'type_id' in self.request.GET:
                    self.type_id = self.request.GET.get('type_id', '')
                    if self.type_id:
                        filters = Q(type=self.type_id)
                        query = query.filter(filters)
                else:
                    self.type_id = ''

                if 'q' in self.request.GET:
                    self.q = self.request.GET.get('q', '')
                    if self.q:
                        query = query.filter(
                            Q(name__icontains=self.q) | Q(
                                code__icontains=self.q)
                        )
                else:
                    self.q = ''
                return query.distinct()

            def get_context_data(self, **kwargs):
                context = ListView.get_context_data(self, **kwargs)
                context['q'] = self.q or ''
                context['type_id'] = self.type_id or ''
                return context

        self.list = ObjectListView.as_view(
            model=self.model,
            paginate_by=10,
            ordering=['code'],
            template_name=self.template_name_base + "_list.html"
        )

    def get_urls(self):
        return [
            path("list", self.list,
                name="objectview_list"),
            path("create", self.create,
                name="objectview_create"),
            path("edit/<int:pk>", self.edit,
                name="objectview_update"),
            path("delete/<int:pk>", self.delete,
                name="objectview_delete"),

        ]


class SustanceCharacteristicsForm(ModelForm):
    class Meta:
        model = SustanceCharacteristics
        fields = '__all__'


@login_required

def block_notifications(request, lab_pk, obj_pk):
    laboratory = Laboratory.objects.get(pk=lab_pk)
    object = Object.objects.get(pk=obj_pk)
    BlockedListNotification.objects.get_or_create(
        laboratory=laboratory, object=object, user=request.user)
    messages.success(request, "You won't be recieving notifications of this object anymore.")
    return render(request, 'laboratory/block_object_notification.html')

