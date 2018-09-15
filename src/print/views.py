'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.http.response import JsonResponse
from print.models import PaperType, Print
from django.db.models.query_utils import Q
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _
from cruds_adminlte.crud import CRUDView
from print.forms import FormPrint
from django.urls.base import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render
from print.models import Print


def index_print(request):
    return render(request, 'index_print.html')


def get_list_print(request):
    q = request.GET.get('search[value]')
    length = request.GET.get('length', '10')
    pgnum = request.GET.get('start', '0')

    try:
        length = int(length)
        pgnum = 1 + (int(pgnum) / length)
    except:
        length = 10
        pgnum = 1

    if q:
        objs = Print.objects.filter(
            Q(name__icontains=q) | Q(location__icontains=q)
        ).order_by('name')
    else:
        objs = Print.objects.all().order_by('name')

    recordsFiltered = objs.count()
    p = Paginator(objs, length)
    if pgnum > p.num_pages:
        pgnum = 1
    page = p.page(pgnum)
    data = []
    for obj in page.object_list:
        data.append([
            obj.id,
            obj.name,
            obj.email,
            #            get_download_links(request, obj)
        ])
    dev = {
        "data": data,
        "recordsTotal": Print.objects.all().count(),
        "recordsFiltered": recordsFiltered
    }

    draw = request.GET.get('_', '')
    try:
        draw = int(draw)
        dev['draw'] = draw
    except:
        pass
    return JsonResponse(dev)


class PrintCRUD(CRUDView):
    model = Print
    views_available = ['create', 'delete', 'update', 'detail']
    namespace = "print"
    add_form = FormPrint

    def get_create_view(self):
        CreateViewClass = super(PrintCRUD, self).get_create_view()

        class OCreateView(CreateViewClass):
            def get_success_url(self):
                url = reverse("print:index_print")
                messages.success(self.request,
                                 _("Your Print was register successfully"))
                return url
        return OCreateView
