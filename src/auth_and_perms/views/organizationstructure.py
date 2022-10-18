from django.shortcuts import render


def organization_manage_view(request):
    return render(request, 'auth_and_perms/list_organizations.html')