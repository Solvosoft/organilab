'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.http.response import JsonResponse
from printOrderManager.models import PaperType, PrintObject
from django.db.models.query_utils import Q
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _
from cruds_adminlte.crud import CRUDView
from printOrderManager.forms import FormPrintObject
from django.urls.base import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render
# TEST
from django.views.generic import FormView
from printOrderManager.forms import PrintLoginForm, PrintRegisterForm
# END TEST


def index_printOrderManager(request):
    return render(request, 'index_printOrderManager.html')


def index_printManager(request):
    return render(request, 'index_printManager.html')


def get_list_printObject(request):
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
        objs = PrintObject.objects.filter(
            Q(name__icontains=q) | Q(location__icontains=q)
        ).order_by('name')
    else:
        objs = PrintObject.objects.all().order_by('name')

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
            # get_download_links(request, obj)
        ])
    dev = {
        "data": data,
        "recordsTotal": PrintObject.objects.all().count(),
        "recordsFiltered": recordsFiltered
    }

    draw = request.GET.get('_', '')
    try:
        draw = int(draw)
        dev['draw'] = draw
    except:
        pass
    return JsonResponse(dev)

# Agregar permisos a modelo, con base a  laboratory. """


class PrintObjectCRUD(CRUDView):
    model = PrintObject
    views_available = ['create', 'delete', 'update', 'detail']
    namespace = "printOrderManager"  # Necesario, si se pone en URL
    add_form = FormPrintObject

    def get_create_view(self):
        CreateViewClass = super(PrintObjectCRUD, self).get_create_view()

        class OCreateView(CreateViewClass):
            def get_success_url(self):
                url = reverse("printOrderManager:index_printOrderManager")
                messages.success(self.request,
                                 _("Your Print was register successfully"))
                return url
        return OCreateView


class PrintLogin(FormView):
    template_name = 'loginRegister/loginPrint.html'
    form_class = PrintLoginForm


class PrintRegister(FormView):
    template_name = 'loginRegister/registerPrint.html'
    form_class = PrintRegisterForm
