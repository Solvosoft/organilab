
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO



# Create your views here.
def ReportBuilding(request):
    # Create the HttpResponse with PDF.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Report-Building.pdf"'

    # Create the PDF object, using the BytesIO object as its "file."
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # Draw things on the PDF. Here's where the PDF generation happens.
    
    #PDF Header
    hora = timezone.now()
    p.setLineWidth(.3)
    p.setFont('Helvetica', 18)
    p.drawString(30, 750, "Report Building")
    p.setFont('Helvetica', 12)
    p.drawString(460, 750, hora.strftime('%d/%m/%Y - %H:%M'))
    p.line(30, 747, 560, 747)

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
    