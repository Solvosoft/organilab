'''
Created on /8/2016

@author: natalia
'''
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.urls import reverse_lazy

from laboratory.views.djgeneric import CreateView, UpdateView, DeleteView
from laboratory.models import ObjectFeatures

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


class FeatureUpdateView(UpdateView):
    model = ObjectFeatures
    fields = '__all__'

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy('laboratory:object_feature_create', kwargs={'lab_pk': self.lab})
        return super(FeatureUpdateView, self).get_success_url()

class FeatureDeleteView(DeleteView):
    model = ObjectFeatures

    def get_success_url(self):
        if self.lab is not None:
            return reverse_lazy('laboratory:object_feature_create', kwargs={'lab_pk': self.lab})
        return super(FeatureDeleteView, self).get_success_url()