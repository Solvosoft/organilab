from django.shortcuts import render

def index_tutorial(request):
    return render(request, 'tutorial.html')
