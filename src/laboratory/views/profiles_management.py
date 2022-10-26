from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.views.generic import ListView, FormView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from laboratory.models import Laboratory
from laboratory.forms import ProfileForm
from laboratory.decorators import has_lab_assigned
from auth_and_perms.models import Profile,Rol,ProfilePermission

@method_decorator(has_lab_assigned(), name="dispatch")
@method_decorator(permission_required('laboratory.view_profile'), name='dispatch')
class ProfilesListView(ListView):
    model = Profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profiles'] = Profile.objects.filter(laboratories__id=self.kwargs['lab_pk'])
        context['lab_pk'] = self.kwargs['lab_pk']
        context['laboratory'] = self.kwargs['lab_pk']
        return context

@method_decorator(has_lab_assigned(lab_pk='pk'), name="dispatch")
@method_decorator(permission_required('laboratory.change_profile'), name='dispatch')
class ProfileUpdateView(FormView, LoginRequiredMixin):
    template_name = 'laboratory/profile_form.html'
    form_class = ProfileForm
    model = Profile
    lab_pk_field = 'pk'

    def get_context_data(self, **kwargs):
        context = dict()
        profile = Profile.objects.filter(pk=self.kwargs['profile_pk']).first()

        context['profile_form'] = ProfileForm(initial=
            {
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'id_card': profile.id_card,
                'job_position': profile.job_position,
                'profile_id': profile.id
            }
        )
        permissions=ProfilePermission.objects.filter(profile__id=profile.id,
                                                     content_type=ContentType.objects.get(
                                                         app_label='laboratory',
                                                         model="laboratory"),
                                                     object_id=self.kwargs['pk']).first()
        roles=list
        if permissions is not None:
            roles=permissions.rol.all()
        context['lab_pk'] = self.kwargs['pk']
        context['laboratory'] = self.kwargs['pk']
        context['profile_pk'] = profile.id
        context['roles'] = Rol.objects.all()
        context['pp']=roles
        return context

    def get_success_url(self, **kwargs):
        lab_pk = self.kwargs['pk']
        success_url = f'/lab/{lab_pk}/profiles/list'
        return success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        profile_id = form.cleaned_data.get('profile_id')
        profile = Profile.objects.get(pk=profile_id)

        profile.id_card = form.cleaned_data.get('id_card')
        profile.job_position = form.cleaned_data.get('job_position')
        profile.user.first_name = form.cleaned_data.get('first_name')
        profile.user.last_name = form.cleaned_data.get('last_name')
        profile.user.save()
        profile.save()
        pp, created = ProfilePermission.objects.get_or_create(profile=profile,
                                                              content_type=ContentType.objects.get(
                                                                  app_label='laboratory',
                                                                  model="laboratory"),
                                                              object_id=self.kwargs['pk'])

        if pp is not None:
            pp.rol.clear()
            roles = self.request.POST.getlist('roles')

            for rol in roles:
                pp.rol.add(rol)

        return response
