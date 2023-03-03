from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.models import User
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView
from django.shortcuts import get_object_or_404
from auth_and_perms.models import Profile
from django.utils.translation import gettext_lazy as _
from authentication.forms import PasswordChangeForm, EditUserForm
from django.http import JsonResponse


@method_decorator(permission_required("auth.change_user"), name="dispatch")
class ChangeUser(UpdateView):
    model = User
    form_class = EditUserForm
    template_name = "auth/change_user.html"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not int(self.kwargs['pk']) == request.user.pk:
            return HttpResponseNotFound('<h1>Page not found</h1>')
        else:
            return response

    def get_success_url(self):
        return reverse_lazy('laboratory:profile', args=(self.kwargs['pk'],))

    def get_context_data(self, **kwargs):
        context = super(ChangeUser, self).get_context_data()
        context['password_form'] = PasswordChangeForm(user=self.object)
        return context

    def form_valid(self, form):
        instance = form.save()
        return super(ChangeUser, self).form_valid(form)

@login_required
@permission_required("auth_and_perms.view_profile")
def get_profile(request, *args, **kwargs):
    org=kwargs.get('org_pk')
    profile = get_object_or_404(Profile, user__pk=kwargs.get('pk'))
    context={
        'org_pk':org,
        'profile':profile
    }
    return render(request,'laboratory/profile_detail.html', context=context)

@permission_required("auth.change_user")
@sensitive_post_parameters('password', 'password_confirm')
@require_http_methods(["POST"])
def password_change(request, pk):
    response = {}
    if request.user.pk == pk:
        user = request.user
        form = PasswordChangeForm(request.POST, user=request.user)
        if form.is_valid():
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            login(request, user)
            messages.success(request, _("Password was changed successfully"))
            response['result'] = "ok"
        else:
            response['errors'] = form.errors
        return JsonResponse(response)
    else:
        return HttpResponseNotFound(_("User is trying to update data doesn't belong to him"))
