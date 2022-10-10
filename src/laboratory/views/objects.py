# encoding: utf-8

'''
Free as freedom will be 26/8/2016

@author: luisza
'''

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.db.models.query_utils import Q
from django.forms import ModelForm
from django.shortcuts import render
from django.urls import path
from django.urls.base import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from djgentelella.forms.forms import CustomForm
from djgentelella.widgets import core as genwidget
from laboratory.models import Laboratory, BlockedListNotification
from laboratory.models import Object, SustanceCharacteristics
from laboratory.utils import filter_laboratorist_profile
from laboratory.views.djgeneric import CreateView, DeleteView, UpdateView, ListView
from laboratory.decorators import has_lab_assigned


class ObjectView(object):
    model = Object
    template_name_base = "laboratory/objectview"

    def __init__(self):
        @method_decorator(has_lab_assigned(), name='dispatch')
        @method_decorator(permission_required('laboratory.add_object'), name='dispatch')
        class ObjectCreateView(CreateView):
            permission_required = ('laboratory.add_object',)
            
            def get_success_url(self, *args, **kwargs):
                redirect = reverse_lazy('laboratory:objectview_list', args=(
                    self.lab,)) + "?type_id=" + self.object.type
                return redirect

            def get_form_kwargs(self):
                kwargs = super(ObjectCreateView, self).get_form_kwargs()
                kwargs['request'] = self.request
                return kwargs

        self.create = ObjectCreateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html",
        )

        @method_decorator(has_lab_assigned(), name='dispatch')
        @method_decorator(permission_required('laboratory.change_object'), name='dispatch')
        class ObjectUpdateView(UpdateView):

            def get_success_url(self):
                return reverse_lazy(
                    'laboratory:objectview_list',
                    args=(self.lab,)) + "?type_id=" + self.get_object().type

            def get_form_kwargs(self):
                kwargs = super(ObjectUpdateView, self).get_form_kwargs()
                kwargs['request'] = self.request
                return kwargs


        self.edit = ObjectUpdateView.as_view(
            model=self.model,
            form_class=ObjectForm,
            template_name=self.template_name_base + "_form.html"
        )

        @method_decorator(has_lab_assigned(), name='dispatch')
        @method_decorator(permission_required('laboratory.delete_object'), name='dispatch')
        class ObjectDeleteView(DeleteView):

            def get_success_url(self):
                return reverse_lazy('laboratory:objectview_list',
                                    args=(self.lab,))

        self.delete = ObjectDeleteView.as_view(
            model=self.model,
            success_url="/",
            template_name=self.template_name_base + "_delete.html"
        )

        
        @method_decorator(has_lab_assigned(), name='dispatch')
        @method_decorator(permission_required('laboratory.view_object'), name='dispatch')    
        class ObjectListView(ListView):

            def get_queryset(self):
                query = ListView.get_queryset(self).filter(
                    Q(laboratory__in = [self.lab])|Q(is_public=True)
                )

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
                return query.distinct()

            def get_context_data(self, **kwargs):
                context = ListView.get_context_data(self, **kwargs)
                context['q'] = self.q or ''
                context['type_id'] = self.type_id or ''
                return context

        self.list = ObjectListView.as_view(
            model=self.model,
            paginate_by=10,
            ordering=['code'],
            template_name=self.template_name_base + "_list.html"
        )

    def get_urls(self):
        return [
            path("list", self.list,
                name="objectview_list"),
            path("create", self.create,
                name="objectview_create"),
            path("edit/<int:pk>/", self.edit,
                name="objectview_update"),
            path("delete/<int:pk>", self.delete,
                name="objectview_delete"),

        ]


class SustanceCharacteristicsForm(ModelForm):
    class Meta:
        model = SustanceCharacteristics
        fields = '__all__'


class ObjectForm(CustomForm,ModelForm):
    required_css_class = ''

    def __init__(self, *args, **kwargs):
        self.request = None
        if 'request' in kwargs:
            self.request = kwargs.pop('request')

        data_type = None
        if 'data' in kwargs:
            data_type = kwargs.get('data').get('type')

        super(ObjectForm, self).__init__(*args, **kwargs)

        self.fields['laboratory'].queryset = filter_laboratorist_profile(self.request.user)
        self.fields['laboratory'].label = _("Available only on this laboratories if it is private")
        if self.request:
            if 'type_id' in self.request.GET:
                self.type_id = self.request.GET.get('type_id', '')
                if self.type_id:
                    self.fields['type'] = forms.CharField(
                        initial=self.type_id,
                        widget=forms.HiddenInput()
                    )
                data_type = self.type_id

        if data_type == Object.EQUIPMENT:
            self.fields['model'].required = True
        else:
            self.fields['model'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['serie'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )
            self.fields['plaque'] = forms.CharField(
                widget=forms.HiddenInput(), required=False
            )

    class Meta:
        model = Object
        fields = '__all__'
        widgets = {
            'features': genwidget.SelectMultiple,
            'laboratory': genwidget.SelectMultiple,
            'code': genwidget.TextInput,
            'name': genwidget.TextInput,
            'synonym':  genwidget.TextInput,
            'is_public': genwidget.YesNoInput,
            'description': genwidget.Textarea
        }


@login_required
@has_lab_assigned()
def block_notifications(request, lab_pk, obj_pk):
    laboratory = Laboratory.objects.get(pk=lab_pk)
    object = Object.objects.get(pk=obj_pk)
    BlockedListNotification.objects.get_or_create(
        laboratory=laboratory, object=object, user=request.user)
    messages.success(request, "You won't be recieving notifications of this object anymore.")
    return render(request, 'laboratory/block_object_notification.html')
