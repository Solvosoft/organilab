from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.utils import timezone
from laboratory.models import LaboratoryRoom, Furniture, Object
from django.template.loader import get_template
from django.template.context import Context
from weasyprint import HTML

from django.views.generic.edit import CreateView


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
    fields = '__all__'
