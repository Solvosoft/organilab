from django.shortcuts import render

from auth_and_perms.forms import MergeUsers


def users_list(request):
     merge_form = MergeUsers(user_session=request.user.pk)
     return render(request,"auth_and_perms/users_list.html", context={
         "merge_form": merge_form})

def merge_users(request, user_base, user_delete):
    return render(request, "auth_and_perms/merge_users.html", context={})
