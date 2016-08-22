
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.utils import timezone
from laboratory.models import LaboratoryRoom, Furniture, Object
from django.template.loader import get_template
from django.template.context import Context
from weasyprint import HTML

class miContexto(object):
    
    def get_context_data(self, **kwargs):
        contex = ListView.get_context_data(self, **kwargs)
        contex['datetime'] = timezone.now()
        return contex

class LaboratoryRoomListView(miContexto, ListView):
    model = LaboratoryRoom
    
class ObjectListView(miContexto, ListView):
    model = Object
    
class FurnitureListView(miContexto, ListView):
    model = Furniture

    
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
    #pisaStatus = pisa.CreatePDF(html, dest=response)
    response = HttpResponse(page, content_type='application/pdf')
    response[
              'Content-Disposition'] = 'attachment; filename="report_building.pdf"'
    return response

def report_objects(request):
    objects = Object.objects.all()

    template = get_template('pdf/object_pdf.html')
    
    context = {
               'object_list': objects,
               'datetime': timezone.now(),
               'request': request
               }
    
    html = template.render(
                            Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()
    #pisaStatus = pisa.CreatePDF(html, dest=response)
    response = HttpResponse(page, content_type='application/pdf')
    response[
              'Content-Disposition'] = 'attachment; filename="report_objects.pdf"'
    return response

def report_furniture(request):
    furniture = Furniture.objects.all()

    template = get_template('pdf/furniture_pdf.html')
    
    context = {
               'object_list': furniture,
               'datetime': timezone.now(),
               'request': request
               }
    
    html = template.render(
                            Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()
    #pisaStatus = pisa.CreatePDF(html, dest=response)
    response = HttpResponse(page, content_type='application/pdf')
    response[
              'Content-Disposition'] = 'attachment; filename="report_furniture.pdf"'
    return response

def report_sumfurniture(request):
    sumfurniture = Furniture.objects.all()

    template = get_template('pdf/summaryfurniture_pdf.html')
    
    context = {
               'object_list': sumfurniture,
               'datetime': timezone.now(),
               'request': request
               }
    
    html = template.render(
                            Context(context)).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()
    #pisaStatus = pisa.CreatePDF(html, dest=response)
    response = HttpResponse(page, content_type='application/pdf')
    response[
              'Content-Disposition'] = 'attachment; filename="report_summaryfurniture.pdf"'
    return response
