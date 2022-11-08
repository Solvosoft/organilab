# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
from django.http import Http404, HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.views.generic import DetailView as djDetailView
from django.views.generic.edit import CreateView as djCreateView
from django.views.generic.edit import DeleteView as djDeleteView
from django.views.generic.edit import UpdateView as djUpdateView
from django.views.generic.list import ListView as djListView
from xhtml2pdf import pisa
from django.conf import settings
from django.contrib.staticfiles import finders
import os
import django_excel
from weasyprint import HTML

#Convert html URI to absolute
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path=result[0]
    else:
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise Exception(
            'media URI must start with %s or %s' % (sUrl, mUrl)
        )
    return path




class CreateView(djCreateView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djCreateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djCreateView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djCreateView.get_context_data(self, **kwargs)
        context['laboratory'] = int(self.lab)
        return context


class UpdateView(djUpdateView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djUpdateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djUpdateView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djUpdateView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        return context


class DeleteView(djDeleteView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djDeleteView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djDeleteView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djDeleteView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        return context


class ListView(djListView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djListView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djListView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['datetime'] = timezone.now()
        return context

class DetailView(djDetailView):
    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        return djDetailView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djDetailView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['datetime'] = timezone.now()
        return context

class ReportListView(djListView):
    file_name = 'document'
    # pdf_template

    def get(self, request, *args, **kwargs):
        self.lab = kwargs['lab_pk']
        self.request_format = request.GET.get('format', 'html')

        if self.request_format=='html':
            return djListView.get(self, request, *args, **kwargs)
        if hasattr(self, 'get_'+self.request_format):
            return getattr(self, 'get_'+self.request_format)(request, *args, **kwargs)
        raise Http404()

    def get_context_data(self, **kwargs):
        context = djListView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['datetime'] = timezone.now()
        return context

    def get_pdf(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        template = get_template(self.get_pdf_template())
        # added explicit context
        html = template.render(context=context)

        page = HTML(string=html, encoding='utf-8').write_pdf()

        response = HttpResponse(page, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.pdf"'%self.get_file_name(request)
        return response

    def get_file_name(self, request):
        return self.file_name


    def get_xls(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        file_format = 'xls'
        return django_excel.make_response_from_array(
            self.get_book(context), file_format, file_name="%s.xls" % self.get_file_name(request))

    def get_xlsx(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        file_format = 'xlsx'
        return django_excel.make_response_from_array(
            self.get_book(context), file_format, file_name="%s.xlsx" % self.get_file_name(request))

    def get_ods(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        file_format = 'ods'
        return django_excel.make_response_from_array(
            self.get_book(context), file_format, file_name="%s.ods" % self.get_file_name(request))

    def get_book(self, context):
        raise NotImplementedError()

    def get_pdf_template(self):
        if hasattr(self, 'pdf_template'):
            return self.pdf_template
        raise RuntimeError('self.pdf_template not found')


class ResultQueryElement(object):
    def __init__(self, data):
        self.__data = data

    def __getattr__(self, item):
        if item in self.__data:
            return self.__data[item]