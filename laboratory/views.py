from django import forms
from django.contrib.auth.decorators import login_required
from django.core.validators import RegexValidator
from django.http import HttpResponse
from django.shortcuts import render
from django.template.context import Context
from django.template.loader import get_template, render_to_string
from django.urls.base import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
import json

from laboratory.models import LaboratoryRoom, Furniture, Object, Shelf, Laboratory
from laboratory.shelf_utils import get_dataconfig
from laboratory.decorators import verify_laboratory_session
from weasyprint import HTML


class miContexto(object):
    def get_context_data(self, **kwargs):
        contex = ListView.get_context_data(self, **kwargs)
        contex['datetime'] = timezone.now()
        return contex

@method_decorator(verify_laboratory_session, name='dispatch')
@method_decorator(login_required, name='dispatch')
class LaboratoryRoomListView(miContexto, ListView):
    model = LaboratoryRoom
    template_name = "laboratory/report_laboratoryroom_list.html"

    def get_queryset(self):
        if 'lab_pk' in self.kwargs:
            lab = get_object_or_404(Laboratory, pk=self.kwargs.get('lab_pk'))
            return lab.rooms.all()
        return super(LaboratoryRoomListView, self).get_queryset()


@method_decorator(login_required, name='dispatch')
class ObjectListView(miContexto, ListView):
    model = Object


@verify_laboratory_session
@login_required
def report_building(request, *args, **kwargs):
    if 'lab_pk' in kwargs:
        rooms = get_object_or_404(Laboratory, pk=self.kwargs.get('lab_pk')).rooms.all()
    else:
        rooms = LaboratoryRoom.objects.all()

    template = get_template('pdf/laboratoryroom_pdf.html')

    context = {
        'object_list': rooms,
        'datetime': timezone.now(),
        'request': request
    }

    html = template.render(Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_building.pdf"'
    return response


@verify_laboratory_session
@login_required
def report_objects(request, *args, **kwargs):
    var = request.GET.get('pk')
    if var is None:
        if 'lab_pk' in kwargs:
            objects = Object.objects.filter(shelfobject__shelf__furniture__labroom__laboratory__pk=kwargs.get('lab_pk'))
        else:
            objects = Object.objects.all()
    else:
        objects = Object.objects.filter(pk=var)

    template = get_template('pdf/object_pdf.html')

    context = {
        'object_list': objects,
        'datetime': timezone.now(),
        'request': request
    }

    html = template.render(
        Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_objects.pdf"'
    return response


@verify_laboratory_session
@login_required
def report_furniture(request, *args, **kwargs):
    var = request.GET.get('pk')
    if var is None:
        if 'lab_pk' in kwargs:
            furniture = Furniture.objects.filter(labroom__laboratory__pk=kwargs.get('lab_pk'))
        else:
            furniture = Furniture.objects.all()
    else:
        furniture = Furniture.objects.filter(pk=var)

    template = get_template('pdf/summaryfurniture_pdf.html')

    context = {
        'object_list': furniture,
        'datetime': timezone.now(),
        'request': request
    }

    html = template.render(
        Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_summaryfurniture.pdf"'
    return response

@verify_laboratory_session
@login_required
def report_reactive_precursor_objects(request, *args, **kwargs):
    template = get_template('pdf/reactive_precursor_objects_pdf.html')

    if 'lab_pk' in kwargs:
        rpo = Object.objects.filter(shelfobject__shelf__furniture__labroom__laboratory__pk=kwargs.get('lab_pk'))
    else:
        rpo = Object.objects.all()

    # Reactive precursor objects
    rpo = rpo.filter(type=Object.REACTIVE, is_precursor=True)

    context = {
        'rpo': rpo,
        'datetime': timezone.now(),
        'request': request
    }

    html = template.render(Context(context)).encode('UTF-8')

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report_reactive_precursor_objects.pdf"'
    return response


@verify_laboratory_session
def index(request):
    return render(request, 'laboratory/index.html')


@method_decorator(login_required, name='dispatch')
class FurnitureListView(miContexto, ListView):
    model = Furniture
    template_name = "laboratory/report_furniture_list.html"

    def get_queryset(self):
        if 'lab_pk' in self.kwargs:
            return Furniture.objects.filter(labroom__furniture=self.kwargs.get('lab_pk'))
        return super(FurnitureListView, self).get_queryset()


@method_decorator(verify_laboratory_session, name='dispatch')
@method_decorator(login_required, name='dispatch')
class FurnitureCreateView(CreateView):
    model = Furniture
    fields = ("labroom", "name", "type")

    def get_success_url(self):
        if 'lab_pk' in self.kwargs:
            return reverse_lazy('laboratory:laboratory_furniture_create',
                                kwargs={'lab_pk': self.kwargs.get('lab_pk')})
        return reverse_lazy("laboratory:furniture_update", kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = CreateView.get_context_data(self, **kwargs)
        if 'lab_pk' in self.kwargs:
            lab = get_object_or_404(Laboratory, pk=self.kwargs.get('lab_pk'))
            context['object_list'] = lab.rooms.all()
            context['lab_pk'] = self.kwargs.get('lab_pk')
        context['object_list'] = self.model.objects.all()
        return context


class FurnitureForm(forms.ModelForm):
    dataconfig = forms.CharField(
        widget=forms.HiddenInput,
        validators=[RegexValidator(
            r'^[\[\],\s"\d]*$',
            message=_("Invalid format in shelf dataconfig "),
            code='invalid_format')])

    class Meta:
        model = Furniture
        fields = ("labroom", "name", "type", 'dataconfig')


@method_decorator(verify_laboratory_session, name='dispatch')
@method_decorator(login_required, name='dispatch')
class FurnitureUpdateView(UpdateView):
    model = Furniture
    success_url = reverse_lazy("laboratory:furniture_create")
    form_class = FurnitureForm

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['dataconfig'] = self.build_configdata()
        return context

    def get_dataconfig(self):
        dataconfig = self.object.dataconfig
        return get_dataconfig(dataconfig)

    def build_configdata(self):
        dataconfig = self.get_dataconfig()
        row = len(dataconfig)
        if row > 0:
            col = len(dataconfig[0])
        else:
            col = 0
        return render_to_string('laboratory/dataconfig.html',
                                {'dataconfig': dataconfig,
                                 'obj': self.object,
                                 'col': col,
                                 'row': row})

    def get_success_url(self):
        if 'lab_pk' in self.kwargs:
            return reverse_lazy('laboratory:laboratory_furniture_create',
                                kwargs={'lab_pk': self.kwargs.get('lab_pk')})
        return super(FurnitureUpdateView, self).get_success_url()


@method_decorator(verify_laboratory_session, name='dispatch')
@method_decorator(login_required, name='dispatch')
class FurnitureDelete(DeleteView):
    model = Furniture
    success_url = reverse_lazy("laboratory:furniture_create")

    def get_success_url(self):
        lab_pk = self.object.labroom.laboratory_set.first().pk
        if lab_pk is not None:
            return reverse_lazy('laboratory:laboratory_furniture_create', kwargs={'lab_pk': lab_pk})
        return super(FurnitureDelete, self).get_success_url()

@method_decorator(verify_laboratory_session, name='dispatch')
@method_decorator(login_required, name='dispatch')
class ReactivePrecursorObjectList(ListView):
    model = Object
    template_name = 'laboratory/reactive_precursor_objects_list.html'

    def get_queryset(self):
        lab_pk = self.kwargs.get('lab_pk')
        return Object.objects.filter(type=Object.REACTIVE, is_precursor=True, shelfobject__shelf__furniture__labroom__laboratory=lab_pk)

    def get_context_data(self, **kwargs):
        context = super(ReactivePrecursorObjectList, self).get_context_data(**kwargs)
        if 'lab_pk' in self.kwargs:
            context['lab_pk'] = self.kwargs.get('lab_pk')
        return context
