'''
Created on /8/2016

@author: natalia
'''
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView

from django_ajax.decorators import ajax
from django_ajax.mixin import AJAXMixin
from laboratory.models import ObjectFeatures


@login_required
def list_objectfeatures_render(request):
    objectfeatures = ObjectFeatures.objects.all()
    return render_to_string(
        'laboratory/objectfeatures_list.html',
        context={
            'object_list': objectfeatures
        })

@login_required
@ajax
def list_objectfeatures(request):
    return {
        'inner-fragments': {
            '#objectfeatures': list_objectfeatures_render(request)
        },
    }


@method_decorator(login_required, name='dispatch')
class ObjectFeaturesCreate(AJAXMixin, CreateView):
    model = ObjectFeatures
    fields = "__all__"
    success_url = reverse_lazy('laboratory:objectfeatures_list')

    def post(self, request, *args, **kwargs):
        response = CreateView.post(self, request, *args, **kwargs)

        if type(response) == HttpResponseRedirect:
            return list_objectfeatures_render(request)

        return response
