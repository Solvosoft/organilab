from django.shortcuts import render

def index_tutorial(request, org_pk):
    return render(request, 'tutorial.html', context={'org_pk': org_pk})
