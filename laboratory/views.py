from django.shortcuts import render

# Create your views here.
def vistaEdificio(request): 
    return render(request, 'vista_edificio.html') 