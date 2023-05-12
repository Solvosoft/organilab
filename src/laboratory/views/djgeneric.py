# encoding: utf-8
'''
Created on 26/12/2016

@author: luisza
'''
import django_excel
from django.http import Http404, HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from django.views.generic import DetailView as djDetailView
from django.views.generic.edit import CreateView as djCreateView
from django.views.generic.edit import DeleteView as djDeleteView
from django.views.generic.edit import UpdateView as djUpdateView
from django.views.generic.list import ListView as djListView
from weasyprint import HTML
from laboratory.utils import check_user_access_kwargs_org_lab


class CreateView(djCreateView):
    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djCreateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djCreateView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djCreateView.get_context_data(self, **kwargs)
        context['org_pk'] = self.org
        context['laboratory'] = self.lab
        return context


class UpdateView(djUpdateView):

    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djUpdateView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djUpdateView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djUpdateView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['org_pk'] = self.org
        return context


class DeleteView(djDeleteView):
    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djDeleteView.get(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djDeleteView.post(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djDeleteView.get_context_data(self, **kwargs)
        context['org_pk'] = self.org
        context['laboratory'] = self.lab
        return context


class ListView(djListView):
    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djListView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djListView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['org_pk'] = self.org
        context['datetime'] = timezone.now()
        return context

class DetailView(djDetailView):
    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org= int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab= int(kwargs['lab_pk'])
        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()
        return djDetailView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = djDetailView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['org_pk'] = self.org
        context['datetime'] = timezone.now()
        return context

class ReportListView(djListView):
    file_name = 'document'
    # pdf_template

    def get(self, request, *args, **kwargs):
        self.lab = None
        self.org = None
        if 'org_pk' in kwargs:
            self.org = int(kwargs['org_pk'])
        if 'lab_pk' in kwargs:
            self.lab = int(kwargs['lab_pk'])

        if not check_user_access_kwargs_org_lab(self.org, self.lab, request.user):
            raise Http404()

        self.request_format = request.GET.get('format', 'html')

        if self.request_format=='html':
            return djListView.get(self, request, *args, **kwargs)
        if hasattr(self, 'get_'+self.request_format):
            return getattr(self, 'get_'+self.request_format)(request, *args, **kwargs)
        raise Http404()

    def get_context_data(self, **kwargs):
        context = djListView.get_context_data(self, **kwargs)
        context['laboratory'] = self.lab
        context['org_pk'] = self.org
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