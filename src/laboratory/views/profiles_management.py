from django.views.generic import ListView, UpdateView, FormView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from laboratory.decorators import user_group_perms

from laboratory.models import Profile
from laboratory.forms import ProfileForm
from django.views.generic.edit import FormMixin


class ProfilesListView(LoginRequiredMixin, ListView):
    model = Profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profiles'] = Profile.objects.filter(
            laboratories__id=self.kwargs['lab_pk'])
        context['lab_pk'] = self.kwargs['lab_pk']
        return context


class ProfileUpdateView(LoginRequiredMixin, FormView):
    template_name = 'laboratory/profile_form.html'

    def get_context_data(self, **kwargs):
        context = dict()
        profile = Profile.objects.get(pk=self.kwargs['pk'])
        context['profile_form'] = ProfileForm(initial=
            {
                'first_name': profile.user.first_name,
                'last_name': profile.user.last_name,
                'id_card': profile.id_card,
                'job_position': profile.job_position
            }
        )

        return context

    
