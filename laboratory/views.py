from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.utils import timezone
from laboratory.models import LaboratoryRoom, Furniture, Object, Shelf
from django.template.loader import get_template, render_to_string
from django.template.context import Context
from weasyprint import HTML
import json
from django.views.generic.edit import CreateView, UpdateView
from django.urls.base import reverse_lazy


class miContexto(object):

    def get_context_data(self, **kwargs):
        contex = ListView.get_context_data(self, **kwargs)
        contex['datetime'] = timezone.now()
        return contex


class LaboratoryRoomListView(miContexto, ListView):
    model = LaboratoryRoom
    template_name = "laboratory/report_laboratoryroom_list.html"


class ObjectListView(miContexto, ListView):
    model = Object


class FurnitureListView(miContexto, ListView):
    model = Furniture
    template_name = "laboratory/report_furniture_list.html"


def report_building(request):
    laboratoryroom = LaboratoryRoom.objects.all()

    template = get_template('pdf/laboratoryroom_pdf.html')

    context = {
        'object_list': laboratoryroom,
        'datetime': timezone.now(),
        'request': request
    }

    html = template.render(Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()

    response = HttpResponse(page, content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="report_building.pdf"'
    return response


def report_objects(request):

    var = request.GET.get('pk')
    if var is None:
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


def report_furniture(request):

    var = request.GET.get('pk')
    if var is None:
        furniture = Furniture.objects.all()
    else:
        furniture = Furniture.objects.filter(pk=var)

    template = get_template('pdf/furniture_pdf.html')

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
        'Content-Disposition'] = 'attachment; filename="report_furniture.pdf"'
    return response


def report_sumfurniture(request):

    var = request.GET.get('pk')
    if var is None:
        sumfurniture = Furniture.objects.all()
    else:
        sumfurniture = Furniture.objects.filter(pk=var)

    template = get_template('pdf/summaryfurniture_pdf.html')

    context = {
        'object_list': sumfurniture,
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


def index(request):
    return render(request, 'laboratory/index.html')


class FurnitureCreateView(CreateView):
    model = Furniture
    success_url = '/'
    fields = ("labroom", "name", "type")

    def get_success_url(self):

        return reverse_lazy("laboratory:furniture_update", kwargs={'pk': self.object.pk})


class FurnitureUpdateView(UpdateView):
    model = Furniture
    success_url = '/'
    fields = ("labroom", "name", "type")

    def get_context_data(self, **kwargs):
        context = UpdateView.get_context_data(self, **kwargs)
        context['dataconfig'] = self.build_configdata()
        return context

    def get_dataconfig(self):
        dataconfig = self.object.dataconfig
        if dataconfig:
            dataconfig = json.loads(dataconfig)

        for irow, row in enumerate(dataconfig):
            for icol, col in enumerate(row):
                if col:
                    dataconfig[irow][icol] = Shelf.objects.filter(
                        pk__in=col.split(","))
        return dataconfig

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
