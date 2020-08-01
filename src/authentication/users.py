from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, FormView
from django.views.generic.base import ContextMixin

from authentication.forms import CreateUserForm, ChangeUserForm
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
    form_class = ChangeUserForm
    template_name = "auth/change_user.html"

    def get_success_url(self):
        return reverse_lazy('laboratory:profile', args=(self.kwargs['pk'],))

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        user.username = form.cleaned_data['username']
        user.first_name = form.cleaned_data['first_name']
        user.first_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.set_password(form.cleaned_data['password'])
        user.save()
        return response