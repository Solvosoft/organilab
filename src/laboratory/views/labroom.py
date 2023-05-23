# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _

from laboratory.models import LaboratoryRoom, Laboratory
from presentation.utils import build_qr_instance, update_qr_instance
from .djgeneric import CreateView, DeleteView, ListView, UpdateView
from laboratory.forms import ReservationModalForm, AddObjectForm, TransferObjectForm, SubtractObjectForm, \
    LaboratoryRoomForm, FurnitureCreateForm, RoomCreateForm

from ..utils import organilab_logentry


@method_decorator(permission_required('laboratory.view_laboratoryroom'), name='dispatch')
class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom

    def get_queryset(self):
        lab = get_object_or_404(
            Laboratory, pk=self.lab)
        self.request.session['search_lab'] = self.lab
        return lab.rooms.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modal_form_reservation'] = ReservationModalForm()
        context['tranfer_object_form'] = TransferObjectForm(users=self.request.user,lab_send=self.lab, org=self.org)
        context['add_object_form'] = AddObjectForm(lab=self.lab)
        context['subtract_object_form'] = SubtractObjectForm()
        context['options'] = ['Reservation','Add','Transfer','Substract']
        context['user'] = self.request.user
        return context



@method_decorator(permission_required('laboratory.add_laboratoryroom'), name='dispatch')
class LabroomCreate(CreateView):
    model = LaboratoryRoom
    form_class = LaboratoryRoomForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        context['object_list'] = lab.rooms.all()
        context['laboratory'] = self.lab
        context['furniture_form'] = FurnitureCreateForm
        return context

    def generate_qr(self):
        schema = self.request.scheme + "://"
        domain = schema + self.request.get_host()
        url = domain + reverse('laboratory:rooms_list', kwargs={"org_pk": self.org, "lab_pk": self.lab})
        url = url + "#labroom=%d" % self.object.pk
        build_qr_instance(url, self.object, self.org)

    def form_valid(self,form):
        self.object = form.save()
        lab = get_object_or_404(Laboratory, pk=self.lab)
        lab.rooms.add(self.object)
        lab.save()
        self.generate_qr()

        organilab_logentry(self.request.user, self.object, ADDITION, changed_data=form.changed_data,
                           relobj=self.lab)

        return super(LabroomCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.org, self.lab))



@method_decorator(permission_required('laboratory.change_laboratoryroom'), name='dispatch')
class LabroomUpdate(UpdateView):
    model = LaboratoryRoom
    form_class = RoomCreateForm

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['furniture_form'] = FurnitureCreateForm
        return context

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.org, self.lab))

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        if context['object'].laboratory != self.laboratory:
            raise Http404()
        return context

    def form_valid(self,form):
        room = form.save()
        organilab_logentry(self.request.user,  room, CHANGE, changed_data=form.changed_data,
                           relobj=self.lab)
        return super(LabroomUpdate, self).form_valid(form)


@method_decorator(permission_required('laboratory.delete_laboratoryroom'), name='dispatch')
class LaboratoryRoomDelete(DeleteView):
    model = LaboratoryRoom
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.org, self.kwargs.get('lab_pk')))

    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        if not context['object'].laboratory_set.filter(pk=self.lab).exists():
            raise Http404()
        return context

    def form_valid(self, form):
        if self.object.laboratory != self.laboratory:
            raise Http404()
        success_url = self.get_success_url()
        organilab_logentry(self.request.user, self.object, DELETION,
                           relobj=self.lab)
        self.object.delete()
        return HttpResponseRedirect(success_url)



@method_decorator(permission_required('laboratory.view_report'), name='dispatch')
class LaboratoryRoomReportView(ListView):
    model = LaboratoryRoom
    template_name = "laboratory/report_laboratoryroom_list.html"

    def get_queryset(self):
        lab = get_object_or_404(Laboratory, pk=self.lab)
        return lab.rooms.all()


@permission_required('laboratory.change_laboratoryroom')
def rebuild_laboratory_qr(request, org_pk, lab_pk):
    lab = get_object_or_404(Laboratory, pk=lab_pk)
    schema =  request.scheme + "://"
    domain = schema + request.get_host()
    baseurl = domain + reverse('laboratory:rooms_list', kwargs={"org_pk": org_pk, "lab_pk": lab_pk})

    for labroom in lab.rooms.all():
        labroom_url="#labroom=%d"%labroom.pk
        update_qr_instance(baseurl+labroom_url, labroom, org_pk)
        for furniture in labroom.furniture_set.all():
            furnitureurl="&furniture=%d"%furniture.pk
            update_qr_instance(baseurl + labroom_url+furnitureurl, furniture, org_pk)
            for shelf in furniture.shelf_set.all():
                shelfurl="&shelf=%d" % shelf.pk
                update_qr_instance(baseurl + labroom_url + furnitureurl + shelfurl, shelf, org_pk)

    return redirect(reverse('laboratory:rooms_create', kwargs={'org_pk': org_pk, 'lab_pk': lab_pk}))