from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.views.generic import CreateView
from django.conf import settings
from django.core.mail import send_mail

from authentication.forms import CreateUserForm
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