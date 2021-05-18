from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from authentication.forms import CreateUserForm, PasswordChangeForm,EditUserForm
from laboratory.decorators import has_lab_assigned
from laboratory.models import Profile, ProfilePermission, Laboratory


@method_decorator(has_lab_assigned(lab_pk='pk'), name="dispatch")
@method_decorator(permission_required("laboratory.add_organizationusermanagement"), name="dispatch")
class AddUser(CreateView):
    model = User
    form_class = CreateUserForm
    lab_pk_field = 'pk'

    def get_success_url(self):
        return reverse_lazy('laboratory:users_management',
                            args=(self.kwargs['pk'],))

    def send_email(self, user):
        schema = self.request.scheme + "://"
        context = {
            'user': user,
            'domain': schema + self.request.get_host()
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
        user.password = password
        user.save()
        profile = Profile.objects.create(user=user, phone_number=form.cleaned_data['phone_number'],
                                         id_card=form.cleaned_data['id_card'],
                                         job_position=form.cleaned_data['job_position'])
        self.send_email(user)
        profile.laboratories.add(self.kwargs['pk'])
        laboratory = Laboratory.objects.filter(pk=self.kwargs['pk']).first()
        group, created = Group.objects.get_or_create(name="General")
        group.user_set.add(user)
        profile_permission = ProfilePermission.objects.create(profile=profile, laboratories=laboratory)
        roles = form.cleaned_data['rol']
        if roles is not None:
            for rol in roles:
                profile_permission.rol.add(rol)
        return response


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


@method_decorator(permission_required("auth.change_user"), name="dispatch")
@sensitive_post_parameters('password', 'password_confirm')
@require_http_methods(["POST"])
def password_change(request, pk):
    if str(request.user.pk) == pk:
        user = request.user
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            password_confirm = form.cleaned_data['password_confirm']
            if password == password_confirm:
                user.set_password(password)
                user.save()
                login(request, user)
                messages.success(request, "Contraseña cambiada exitosamente.")
            else:
                messages.error(request, "Error al intentar cambiar su contraseña: Las contraseñas deben coincidir.")
        else:
            messages.error(request,
                           "Error al intentar cambiar su contraseña: Asegurese de llenar los campos y que el formato sea correcto.")
        return redirect('laboratory:profile', pk=pk)
    return HttpResponseNotFound('Usuario intentando actualizar un dato que no le pertenece')
