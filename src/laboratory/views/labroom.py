# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _

from laboratory.forms import LaboratoryRoomForm, FurnitureCreateForm, RoomCreateForm
from laboratory.models import LaboratoryRoom, Laboratory
from presentation.utils import build_qr_instance, update_qr_instance
from report.forms import LaboratoryRoomReportForm
from .djgeneric import CreateView, DeleteView, ListView, UpdateView
from ..shelfobject.forms import TransferOutShelfObjectForm, \
    MoveShelfObjectForm, ReserveShelfObjectForm, ShelfObjectRefuseReactiveForm, \
    ShelfObjectMaterialForm, \
    ShelfObjectRefuseMaterialForm, ShelfObjectReactiveForm, \
    ShelfObjectRefuseEquipmentForm, ShelfObjectEquipmentForm, \
    DecreaseShelfObjectForm, IncreaseShelfObjectForm, \
    TransferInShelfObjectApproveWithContainerForm, ContainerManagementForm
from ..shelfobject.serializers import SearchShelfObjectSerializer
from ..utils import organilab_logentry, check_user_access_kwargs_org_lab


@method_decorator(permission_required('laboratory.view_laboratoryroom'),
                  name='dispatch')
class LaboratoryRoomsList(ListView):
    model = LaboratoryRoom

    def get_queryset(self):
        lab = get_object_or_404(Laboratory, pk=self.lab)
        self.request.session['search_lab'] = self.lab
        return lab.laboratoryroom_set.all()

    def get_labroom_data(self, serializer, result):
        if 'labroom' in serializer.validated_data:
            result["labroom"] = [serializer.validated_data['labroom'].pk]

    def get_furniture_data(self, serializer, result):
        if 'furniture' in serializer.validated_data:
            furniture = serializer.validated_data['furniture']
            result["furniture"] = {"furniture": [furniture.pk]}

            if not "labroom" in serializer.validated_data:
                result["labroom"] = [furniture.labroom.pk]

    def get_shelf_data(self, serializer, result):
        if 'shelf' in serializer.validated_data:
            shelf = serializer.validated_data['shelf']
            result["shelf"] = {"shelf": [shelf.pk]}

            if not "furniture" in serializer.validated_data:
                result["furniture"] = {"furniture": [shelf.furniture.pk]}

            if not "labroom" in serializer.validated_data:
                result["labroom"] = [shelf.furniture.labroom.pk]

    def get_shelfobject_data(self, serializer, result):
        if 'shelfobject' in serializer.validated_data:
            shelfobject = serializer.validated_data['shelfobject']
            result["shelfobject"] = {"shelfobject": [shelfobject.pk]}
            result["shelfobject"]["filter_shelfobject"] = True

            if not "shelf" in serializer.validated_data:
                result["shelf"] = {"shelf": [shelfobject.shelf.pk]}

            if not "furniture" in serializer.validated_data:
                result["furniture"] = {"furniture": [shelfobject.shelf.furniture.pk]}

            if not "labroom" in serializer.validated_data:
                result["labroom"] = [shelfobject.shelf.furniture.labroom.pk]

    def search_by_url(self, kwargs):
        result = {}

        if any([i in kwargs for i in ['labroom', 'furniture', 'shelf', 'shelfobject']]):
            serializer = SearchShelfObjectSerializer(data=kwargs, context={
                'source_laboratory_id': self.lab})

            if serializer.is_valid():
                self.get_labroom_data(serializer, result)
                self.get_furniture_data(serializer, result)
                self.get_shelf_data(serializer, result)
                self.get_shelfobject_data(serializer, result)
            else:
                raise Http404()
        return result

    def get_obj_colors(self):
        return {
            'labroom': '#b8e4ff',
            'furniture': '#ff85d5',
            'shelf': '#ffe180',
            'shelfobject': '#95fab9',
            'object': '#f4fab4',
        }


    def get_whitelist_by_object(self, model, filters, color, value='name'):
        suggestions_tag = []
        contenttype = ContentType.objects.filter(
            app_label='laboratory',
            model=model
        ).first()

        MODEL = contenttype.model_class()
        queryset = MODEL.objects.filter(**filters).values('pk', value).distinct()
        whitelist = [
            {'pk': x['pk'], 'value': "%d: %s" % (x['pk'], x[value]), 'objtype': model, 'color': color}
            for x in queryset]

        if whitelist:
            suggestions_tag = suggestions_tag + whitelist
        return suggestions_tag

    def get_suggestions_tag(self):
        color_by_obj = self.get_obj_colors()
        suggestions_tag = self.get_whitelist_by_object('laboratoryroom', {'laboratory': self.lab}, color_by_obj['labroom'])
        suggestions_tag += self.get_whitelist_by_object('furniture', {'labroom__laboratory': self.lab}, color_by_obj['furniture'])
        suggestions_tag += self.get_whitelist_by_object('shelf', {'furniture__labroom__laboratory': self.lab}, color_by_obj['shelf'])
        suggestions_tag += self.get_whitelist_by_object('shelfobject',
                                                        {'in_where_laboratory': self.lab, 'containershelfobject': None},
                                                        color_by_obj['shelfobject'], value='object__name')
        suggestions_tag += self.get_whitelist_by_object('object',
                                                        {'shelfobject__in_where_laboratory': self.lab,
                                                         'shelfobject__containershelfobject': None}, color_by_obj['object'],
                                                        value='name')
        return suggestions_tag

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reserve_object_form'] = ReserveShelfObjectForm(prefix="reserve")
        context['transfer_out_object_form'] = TransferOutShelfObjectForm(
            users=self.request.user, lab_send=self.lab, org=self.org)
        context['increase_object_form'] = IncreaseShelfObjectForm(prefix="increase")
        context['decrease_object_form'] = DecreaseShelfObjectForm(prefix="decrease")
        context['move_object_form'] = MoveShelfObjectForm(prefix="move")
        context['equipment_form'] = ShelfObjectEquipmentForm(initial={"objecttype": 2},
                                                            org_pk=self.org,
                                                            prefix='ef')
        context['equipment_refuse_form'] = ShelfObjectRefuseEquipmentForm(
            initial={"objecttype": 2}, org_pk=self.org, prefix='erf')
        context['reactive_form'] = ShelfObjectReactiveForm(initial={"objecttype": 0},
                                                           org_pk=self.org, prefix="rf",
                                                           modal_id="#reactive_form"
                                                           )
        context['manage_container_form'] = ContainerManagementForm(prefix='mc')
        context['reactive_refuse_form'] = ShelfObjectRefuseReactiveForm(
            initial={"objecttype": 0}, org_pk=self.org, prefix="rff",
            modal_id="#reactive_refuse_form")
        context['material_form'] = ShelfObjectMaterialForm(initial={"objecttype": 1},
                                                           org_pk=self.org, prefix="mf")
        context['material_refuse_form'] = ShelfObjectRefuseMaterialForm(
            initial={"objecttype": 1}, org_pk=self.org, prefix="mff")
        context[
            'transfer_in_approve_with_container_form'] = TransferInShelfObjectApproveWithContainerForm(
            modal_id="#transfer_in_approve_with_container_id_modal", set_container_advanced_options=True)
        context['options'] = ['Reservation', 'Add', 'Transfer', 'Substract']
        context['user'] = self.request.user
        context['search_by_url'] = self.search_by_url(self.request.GET)
        context['suggestions_tag'] = self.get_suggestions_tag()
        context['colors_tooltip'] = render_to_string('laboratory/shelfobject/colors_tooltip.html',
                                                      request=self.request)
        return context


@method_decorator(permission_required('laboratory.add_laboratoryroom'), name='dispatch')
class LabroomCreate(CreateView):
    model = LaboratoryRoom
    form_class = LaboratoryRoomForm
    success_url = "/"

    def get_form_kwargs(self):
        kwargs= super().get_form_kwargs()
        kwargs['initial']={'created_by': self.request.user}
        return kwargs

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        context['object_list'] = lab.laboratoryroom_set.all()
        context['laboratory'] = self.lab
        context['furniture_form'] = FurnitureCreateForm
        return context

    def generate_qr(self):
        schema = self.request.scheme + "://"
        domain = schema + self.request.get_host()
        url = domain + reverse('laboratory:rooms_list',
                               kwargs={"org_pk": self.org, "lab_pk": self.lab})
        url = url + "#labroom=%d" % self.object.pk
        build_qr_instance(url, self.object, self.org)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        lab = get_object_or_404(Laboratory, pk=self.lab)
        self.object.laboratory = lab
        self.object.created_by = self.request.user
        self.object.save()
        self.generate_qr()

        organilab_logentry(self.request.user, self.object, ADDITION,
                           changed_data=form.changed_data,
                           relobj=self.lab)

        return super(LabroomCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.org, self.lab))


@method_decorator(permission_required('laboratory.change_laboratoryroom'),
                  name='dispatch')
class LabroomUpdate(UpdateView):
    model = LaboratoryRoom
    form_class = RoomCreateForm

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['furniture_form'] = FurnitureCreateForm
        return context

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create', args=(self.org, self.lab))

    def get_form_kwargs(self):
        kwargs= super().get_form_kwargs()
        kwargs['initial']={'created_by': self.request.user}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context['object'].laboratory != self.laboratory:
            raise Http404()
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.laboratory = get_object_or_404(Laboratory, pk=self.lab)
        self.object.save()
        organilab_logentry(self.request.user, self.object, CHANGE,
                           changed_data=form.changed_data,
                           relobj=self.lab)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return super().form_invalid(form)


@method_decorator(permission_required('laboratory.delete_laboratoryroom'),
                  name='dispatch')
class LaboratoryRoomDelete(DeleteView):
    model = LaboratoryRoom
    success_url = "/"

    def get_success_url(self):
        return reverse_lazy('laboratory:rooms_create',
                            args=(self.org, self.kwargs.get('lab_pk')))

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context['object'].laboratory != self.laboratory:
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
    template_name = "report/base_report_form_view.html"

    def get_queryset(self):
        self.obj_lab = get_object_or_404(Laboratory, pk=self.lab)
        self.obj_rooms = self.obj_lab.laboratoryroom_set.all()
        return self.obj_rooms

    def get_context_data(self, **kwargs):
        context = super(LaboratoryRoomReportView,
                        self).get_context_data(**kwargs)
        lab_obj = get_object_or_404(Laboratory, pk=self.lab)
        title = _("Objects by Laboratory Room Report")
        context.update({
            'title_view': title,
            'report_urlnames': ['reports_laboratory'],
            'form': LaboratoryRoomReportForm(initial={
                'name': slugify(title + ' ' + now().strftime("%x").replace('/', '-')),
                'title': title,
                'organization': self.org,
                'report_name': 'report_laboratory_room',
                'laboratory': lab_obj,
                'all_labs_org': False
            })
        })
        return context


@permission_required('laboratory.change_laboratoryroom')
def rebuild_laboratory_qr(request, org_pk, lab_pk):
    if not check_user_access_kwargs_org_lab(org_pk, lab_pk, request.user):
        raise Http404()
    lab = get_object_or_404(Laboratory, pk=lab_pk)
    schema = request.scheme + "://"
    domain = schema + request.get_host()
    baseurl = domain + reverse('laboratory:rooms_list',
                               kwargs={"org_pk": org_pk, "lab_pk": lab_pk})

    for labroom in lab.laboratoryroom_set.all():
        labroom_url = "#labroom=%d" % labroom.pk
        update_qr_instance(baseurl + labroom_url, labroom, org_pk)
        for furniture in labroom.furniture_set.all():
            furnitureurl = "&furniture=%d" % furniture.pk
            update_qr_instance(baseurl + labroom_url + furnitureurl, furniture, org_pk)
            for shelf in furniture.shelf_set.all():
                shelfurl = "&shelf=%d" % shelf.pk
                update_qr_instance(baseurl + labroom_url + furnitureurl + shelfurl,
                                   shelf, org_pk)

    return redirect(
        reverse('laboratory:rooms_create', kwargs={'org_pk': org_pk, 'lab_pk': lab_pk}))
