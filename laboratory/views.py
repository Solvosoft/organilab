
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.utils import timezone
from laboratory.models import LaboratoryRoom
from django.template.loader import get_template
from django.template.context import Context
from weasyprint import HTML

class LaboratoryRoomListView(ListView):
    model = LaboratoryRoom
    
def report_building(request):
    laboratoryroom = LaboratoryRoom.objects.all()

    template = get_template('laboratory/laboratoryroom_list.html')
    html = template.render(
                             Context({'object_list': laboratoryroom})).encode("UTF-8")

    page = HTML(string=html, encoding='utf-8').write_pdf()
    #pisaStatus = pisa.CreatePDF(html, dest=response)
    response = HttpResponse(page, content_type='application/pdf')
    response[
              'Content-Disposition'] = 'attachment; filename="report_building.pdf"'
    return response
