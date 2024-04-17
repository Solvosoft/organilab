from django.shortcuts import render


def users_list(request):
     return render(request,"auth_and_perms/users_list.html", context={})
