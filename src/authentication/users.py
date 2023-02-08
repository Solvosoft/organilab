from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView
from django.utils.translation import gettext_lazy as _
from authentication.forms import PasswordChangeForm, EditUserForm


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
        context['password_form'] = PasswordChangeForm()
        return context

    def form_valid(self, form):
        instance = form.save()
        return super(ChangeUser, self).form_valid(form)


@permission_required("auth.change_user")
@sensitive_post_parameters('password', 'password_confirm')
@require_http_methods(["POST"])
def password_change(request, pk):
    if request.user.pk == pk:
        user = request.user
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            password_confirm = form.cleaned_data['password_confirm']
            if password == password_confirm:
                user.set_password(password)
                user.save()
                login(request, user)
                messages.success(request, _("Password was changed successfully"))
            else:
                messages.error(request, _("Error trying to change your password: Passwords should match"))
        else:
            messages.error(request, _("Error trying to change your password: Check fields are filled and correct format"))
        return redirect('laboratory:profile', pk=pk)
    return HttpResponseNotFound(_("User is trying to update data doesn't belong to him"))
