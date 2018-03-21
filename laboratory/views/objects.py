# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
'''

from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from django.forms import ModelForm
from django import forms
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator

#from laboratory.decorators import check_lab_permissions, user_lab_perms
from laboratory.models import Object
from laboratory.views.djgeneric import CreateView, DeleteView, UpdateView, ListView

from laboratory.decorators import user_group_perms, view_user_group_perms

class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):
        @method_decorator(user_group_perms(perm='laboratory.add_object'), name='dispatch')
        class ObjectCreateView(CreateView):

            def get_success_url(self, *args, **kwargs):
                redirect = reverse_lazy('laboratory:objectview_list', args=(
                    self.lab,)) + "?type_id=" + self.object.type
                return redirect

            def get_form_kwargs(self):
                kwargs = super(ObjectCreateView, self).get_form_kwargs()
                kwargs['request'] = self.request
                return kwargs

        self.create = view_user_group_perms(login_required(ObjectCreateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html"
        )),'laboratory.add_object')

        @method_decorator(user_group_perms(perm='laboratory.change_object'), name='dispatch')
        class ObjectUpdateView(UpdateView):

            def get_success_url(self):
                return reverse_lazy(
                    'laboratory:objectview_list',
                    args=(self.lab,)) + "?type_id=" + self.get_object().type

            def get_form_kwargs(self):
                kwargs = super(ObjectUpdateView, self).get_form_kwargs()
                kwargs['request'] = self.request
                return kwargs

        self.edit = view_user_group_perms(login_required(ObjectUpdateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html"
        )),'laboratory.change_object')

        @method_decorator(user_group_perms(perm='laboratory.delete_object'), name='dispatch')
        class ObjectDeleteView(DeleteView):

            def get_success_url(self):
                return reverse_lazy('laboratory:objectview_list',
                                    args=(self.lab,))

        self.delete = view_user_group_perms(login_required(ObjectDeleteView.as_view(
            model=self.model,
            success_url="/",
            template_name=self.template_name_base + "_delete.html"
        )),'laboratory.delete_object')

        @method_decorator(user_group_perms(perm='laboratory.view_object'), name='dispatch')    
        class ObjectListView(ListView):

            def get_queryset(self):
                query = ListView.get_queryset(self)
                if 'type_id' in self.request.GET:
                    self.type_id = self.request.GET.get('type_id', '')
                    if self.type_id:
                        filters = Q(type=self.type_id)
                        query = query.filter(filters)
                else:
                    self.type_id = ''

                if 'q' in self.request.GET:
                    self.q = self.request.GET.get('q', '')
                    if self.q:
                        query = query.filter(
                            Q(name__icontains=self.q) | Q(
                                code__icontains=self.q)
                        )
                else:
                    self.q = ''
                return query

            def get_context_data(self, **kwargs):
                context = ListView.get_context_data(self, **kwargs)
                context['q'] = self.q or ''
                context['type_id'] = self.type_id or ''
                return context

        self.list = view_user_group_perms(login_required(ObjectListView.as_view(
            model=self.model,
            paginate_by=10,
            ordering=['code'],
            template_name=self.template_name_base + "_list.html"
        )),'laboratory.view_object')

    def get_urls(self):
        return [
            url(r"^list$", self.list,
                name="objectview_list"),
            url(r"^create$", self.create,
                name="objectview_create"),
            url(r"^edit/(?P<pk>\d+)$", self.edit,
                name="objectview_update"),
            url(r"^delete/(?P<pk>\d+)$", self.delete,
                name="objectview_delete"),

        ]


class ObjectForm(ModelForm):
    class Meta:
        model = Object
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.request = None
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        data_type = None
        if 'data' in kwargs:
            data_type = kwargs.get('data').get('type')

        super(ObjectForm, self).__init__(*args, **kwargs)

        if self.request:
            if 'type_id' in self.request.GET:
                self.type_id = self.request.GET.get('type_id', '')
                if self.type_id:
                    self.fields['type'] = forms.CharField(
                        initial=self.type_id,
                        widget=forms.HiddenInput()
                    )

        if data_type is not None and data_type == Object.REACTIVE:
            self.fields['molecular_formula'].required = True
            self.fields['cas_id_number'].required = True
            self.fields['security_sheet'].required = True
            self.fields['imdg_code'].required = True
