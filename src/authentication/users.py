from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView

from authentication.forms import CreateUserForm, PasswordChangeForm
from laboratory.decorators import user_group_perms
from laboratory.models import OrganizationUserManagement


@method_decorator(login_required, name='dispatch')
class AddUser(CreateView):
    model = User
    form_class = CreateUserForm

    def get_success_url(self):
        return reverse_lazy('laboratory:users_management',
                            args=(self.kwargs['pk'],))

    def send_email(self,  user):
        schema=self.request.scheme+"://"
        context = {
            'user': user,
            'domain': schema+self.request.get_host()
        }
        send_mail(subject="Nuevo usuario creado en la plataforma",
                  message="Por favor use un visor de html",
                  recipient_list=[user.email],
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  html_message=render_to_string(
                      'gentelella/registration/new_user.html',
                      context=context
                  )
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        password = User.objects.make_random_password()
        form.save()
        user = User.objects.filter(
            username=form.cleaned_data['username']
        ).first()
        user.password=password
        user.save()
        self.send_email(user)
        orga_user_manager = OrganizationUserManagement.objects.filter(organization__pk=self.kwargs['pk']).first()
        if orga_user_manager:
            orga_user_manager.users.add(user)
        return response


@method_decorator(login_required, name='dispatch')
class ChangeUser(UpdateView):

    model = User
    form_class = CreateUserForm
    template_name = "auth/change_user.html"

    def get_success_url(self):
        return reverse_lazy('laboratory:profile', args=(self.kwargs['pk'],))

    def get_context_data(self, **kwargs):
        context = super(ChangeUser, self).get_context_data()
        context['password_form'] = PasswordChangeForm()
        return context


@login_required
def password_change(request, pk):

    user = User.objects.get(pk=pk)

    if request.method == "POST":

        form = PasswordChangeForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data['password']
            password_confirm = form.cleaned_data['password_confirm']

            if password == password_confirm:

                if user.check_password(password):

                    user.set_password(password)
                    user.save()
                    messages.success(request, "Contraseña cambiada exitosamente.")
                    return redirect('laboratory:profile', pk=pk)
                else:
                    messages.error(request, "Error al intentar cambiar su contraseña: Formato incorrecto.")
                    return redirect('laboratory:profile', pk=pk)
            else:
                messages.error(request, "Error al intentar cambiar su contraseña: Las contraseñas deben coincidir.")
                return redirect('laboratory:profile', pk=pk)

        else:
            messages.error(request, "Error al intentar cambiar su contraseña: Asegurese de llenar los campos y que el formato sea correcto.")
            return redirect('laboratory:profile', pk=pk)