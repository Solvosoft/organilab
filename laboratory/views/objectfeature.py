'''
Created on /8/2016

@author: natalia
'''
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from laboratory.decorators import check_lab_permissions, check_user_group
from laboratory.views.djgeneric import CreateView, UpdateView, DeleteView
from laboratory.models import ObjectFeatures

@method_decorator(login_required, name='dispatch')
@method_decorator(check_lab_permissions, name='dispatch')
@method_decorator(check_user_group(group='laboratory_student'), name='dispatch')
class FeatureCreateView(CreateView):
    model = ObjectFeatures
    fields = '__all__'

    def get_context_data(self, **kwargs):
        paginator = Paginator(ObjectFeatures.objects.all().distinct(), 10)
        page = self.request.GET.get('page')

        context = super(FeatureCreateView, self).get_context_data(**kwargs)
        context['create'] = True

        try:
            context['object_list'] = paginator.page(page)
        except PageNotAnInteger:
            context['object_list'] = paginator.page(1)
        except EmptyPage:
            context['object_list'] = paginator.page(paginator.num_pages)

        return context

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy('laboratory:object_feature_create', kwargs={'lab_pk': self.lab})
        return super(FeatureCreateView, self).get_success_url()

@method_decorator(login_required, name='dispatch')
@method_decorator(check_lab_permissions, name='dispatch')
@method_decorator(check_user_group(group='laboratory_student'), name='dispatch')
class FeatureUpdateView(UpdateView):
    model = ObjectFeatures
    fields = '__all__'

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy('laboratory:object_feature_create', kwargs={'lab_pk': self.lab})
        return super(FeatureUpdateView, self).get_success_url()

@method_decorator(login_required, name='dispatch')
@method_decorator(check_lab_permissions, name='dispatch')
@method_decorator(check_user_group(group='laboratory_student'), name='dispatch')
class FeatureDeleteView(DeleteView):
    model = ObjectFeatures

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy('laboratory:object_feature_create', kwargs={'lab_pk': self.lab})
        return super(FeatureDeleteView, self).get_success_url()