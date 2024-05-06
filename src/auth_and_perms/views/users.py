from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404

from auth_and_perms.forms import MergeUsers, UserForm


def users_list(request):
     merge_form = MergeUsers(user_session=request.user.pk)
     return render(request,"auth_and_perms/users_list.html", context={
         "merge_form": merge_form})

def merge_users(request, user_base, user_delete):

    user_base_instance = get_object_or_404(User, pk=user_base)
    user_delete_instance = get_object_or_404(User, pk=user_delete)

    context = {
        "user_base_form": UserForm(instance=user_base_instance, render_type="as_horizontal"),
        "user_delete_form": UserForm(instance=user_delete_instance, render_type="as_horizontal")
    }

    return render(request, "auth_and_perms/merge_users.html", context=context)
