# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
'''

from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from laboratory.models import Object
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls.base import reverse_lazy
from django.forms import ModelForm
from django_ajax.decorators import ajax


class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):
        self.create = login_required(CreateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_form.html"
        ))

        self.edit = login_required(UpdateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_form.html"
        ))

        self.delete = login_required(DeleteView.as_view(
            model=self.model,
            success_url=reverse_lazy('laboratory:objectview_list'),
            template_name=self.template_name_base + "_delete.html"
        ))

        self.list = login_required(ListView.as_view(
            model=self.model,
            paginate_by=10,
            ordering=['code'],
            template_name=self.template_name_base + "_list.html"
        ))

    def get_urls(self):
        return [
            url(r"^objectview/list$", self.list,
                name="objectview_list"),
            url(r"^objectview/create$", self.create,
                name="objectview_create"),
            url(r"^objectview/edit/(?P<pk>\d+)$", self.edit,
                name="objectview_update"),
            url(r"^objectview/delete/(?P<pk>\d+)$", self.delete,
                name="objectview_delete"),

        ]


class ObjectForm(ModelForm):
    class Meta:
        model = Object
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        extended = False
        instance = kwargs.get('instance')
        data_type = Object.REACTIVE
        if 'data' in kwargs:
            data_type = kwargs.get('data').get('type')
        if 'extended' in kwargs:
            extended = kwargs.pop('extended')
        super(ObjectForm, self).__init__(*args, **kwargs)
        if not extended:
            if not instance or instance.type != Object.REACTIVE or data_type != Object.REACTIVE:
                del self.fields['molecular_formula']
                del self.fields['cas_id_number']
                del self.fields['security_sheet']
                del self.fields['is_precursor']
            else:
                self.fields['molecular_formula'].required = True
                self.fields['cas_id_number'].required = True
                self.fields['security_sheet'].required = True


@ajax
@csrf_exempt
def get_extended_form(request, *args, **kwargs):
    extended = int(request.GET['extended'])
    if request.method == 'POST' and request.is_ajax():
        form = ObjectForm(request.POST, extended=bool(extended))
        rendered_form = render_to_string('laboratory/objectview_extended_form.html', context={'form': form},
                                         request=request)
        return rendered_form
