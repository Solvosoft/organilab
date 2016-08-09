from django.shortcuts import render
from reportlab.pdfgen import canvas
from django.http import HttpResponse 
from io import BytesIO
from reportlab.lib.pagesizes import A4

# Create your views here.

def ReportBuilding(request):
    # Create the HttpResponse with PDF.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Report-Building.pdf"'

    # Create the PDF object, using the BytesIO object as its "file."
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # Draw things on the PDF. Here's where the PDF generation happens.
    #Header
    p.setLineWidth(.3)
    p.setFont('Helvetica', 22)
    p.drawString(30, 750, "Report Building")

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
    