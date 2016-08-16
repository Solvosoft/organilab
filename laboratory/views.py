
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.utils import timezone
from laboratory.models import LaboratoryRoom, Furniture
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
    
class SummaryFurnitureListView(miContexto, ListView):
    model = Furniture

    
def report_building(request):
    laboratoryroom = LaboratoryRoom.objects.all()

    template = get_template('laboratory/laboratoryroom_list.html')
    
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

def summary_report(request):
    furniture = Furniture.objects.all()

    template = get_template('laboratory/furniture_list.html')
    
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
              'Content-Disposition'] = 'attachment; filename="report_summaryfurniture.pdf"'
    return response
