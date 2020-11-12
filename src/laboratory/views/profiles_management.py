from django.views.generic import ListView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from laboratory.decorators import user_group_perms

from laboratory.models import Profile


class UsersProfileManagementListView(LoginRequiredMixin, ListView):
    model = Profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profiles'] = Profile.objects.filter(laboratories__id=self.kwargs['lab_pk'])
        return context
        