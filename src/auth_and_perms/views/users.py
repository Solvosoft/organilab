from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from auth_and_perms.forms import MergeUsers, UserForm
from auth_and_perms.utils import user_management


def users_list(request):
     return render(request,"auth_and_perms/users_list.html", context={
         "merge_form": MergeUsers()})

def merge_users(request, user_base, user_delete):
    user_base_instance = get_object_or_404(User, pk=user_base)
    user_delete_instance = get_object_or_404(User, pk=user_delete)

    context = {
        "user_base": user_base,
        "user_delete": user_delete,
        "user_base_form": UserForm(instance=user_base_instance, render_type="as_horizontal", user=request.user),
        "user_delete_form": UserForm(instance=user_delete_instance, render_type="as_horizontal", prefix="delete", user=request.user)
    }

    return render(request, "auth_and_perms/merge_users.html", context=context)


def save_user_merge(request, user_base, user_delete):
    user_base_instance = get_object_or_404(User, pk=user_base)
    user_delete_instance = get_object_or_404(User, pk=user_delete)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user_base_instance, render_type="as_horizontal", user=request.user)

        if form.is_valid():
            form.save()
            user_management(request, user_base_instance, user_delete_instance, "merge")
            messages.success(request, _("Element saved successfully"))
        else:
            context = {
                "user_base": user_base,
                "user_delete": user_delete,
                "user_base_form": form,
                "user_delete_form": UserForm(instance=user_delete_instance,
                                             render_type="as_horizontal", user=request.user)
            }
            return render(request, "auth_and_perms/merge_users.html", context=context)
    return redirect(reverse("auth_and_perms:users_list"))
