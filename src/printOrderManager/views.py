'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.http.response import JsonResponse
from printOrderManager.models import PaperType, PrintObject
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _
from cruds_adminlte.crud import CRUDView
from printOrderManager.forms import FormPrintObject
from django.urls.base import reverse
from django.contrib import messages
from django.shortcuts import render
from django.views.generic import FormView
from printOrderManager.forms import PrintLoginForm, PrintRegisterForm
# Import for login required
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
# Import for messages
from django.contrib import messages

def index_printOrderManager(request):
    return render(request, 'index_printOrderManager.html')

@login_required
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
        objs = PrintObject.objects.all().filter(Q(creation_date__icontains=q) | 
        Q(name__icontains=q) | Q(qualification__icontains=q) | Q(responsible_user__username__icontains=q) | 
        Q(responsible_user__first_name__icontains=q) | Q(responsible_user__last_name__icontains=q), Q(responsible_user_id=request.user.id)).order_by('creation_date')
    else:
        objs = PrintObject.objects.all().filter(
            Q(responsible_user_id=request.user.id)
        ).order_by('creation_date')

    recordsFiltered = objs.count()
    p = Paginator(objs, length)
    if pgnum > p.num_pages:
        pgnum = 1
    page = p.page(pgnum)
    data = []
    for obj in page.object_list:
        cont = 0
        state = ""
        qualification = ""
        user = User.objects.get(pk=obj.responsible_user_id)
        printActions = "<a class='btn btn-info'><span class='glyphicon glyphicon-th-list' aria-hidden='true'></span>&nbsp; "+_('Manage')+"</a>&nbsp;"
        printActions += "<a class='btn btn-danger'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span>&nbsp; "+_('Delete')+"</a>"
        printLogo = "<img class='iconTable' src='http://localhost:8000/media/"+obj.logo.name+"'> &nbsp;&nbsp; " + obj.name
        while cont < obj.qualification:
            qualification += "<img class='iconTable' src='http://localhost:8000/static/images/star.png'>";
            cont += 1
        cont = 0
        while cont < (5-obj.qualification):
            qualification += "<img class='iconTable' src='http://localhost:8000/static/images/whiteStar.png'>";
            cont += 1
        if(user.first_name == ""):
            responsibleUser = user.username
        else:
            responsibleUser = user.first_name+" "+user.last_name+" ("+ user.username+")"
        if(obj.state == ""):
            state = _("<div class='stateA'> Available </div>")
        else:
            state = obj.state
        data.append([
            printLogo,
            state,
            responsibleUser,
            obj.creation_date,
            qualification,
            printActions
            # get_download_links(request, obj)
        ])
    dev = {
        "data": data,
        "recordsTotal": PrintObject.objects.all().filter(Q(responsible_user_id=request.user.id)).count(),
        "recordsFiltered": recordsFiltered
    }

    draw = request.GET.get('_', '')
    try:
        draw = int(draw)
        dev['draw'] = draw
    except:
        pass
    return JsonResponse(dev)


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

# This means the view requiered login
# @login_required -> Login requiered is used in other kind of views


@method_decorator(login_required, name='dispatch')
class PrintRegister(FormView):
    template_name = 'loginRegister/registerPrint.html'
    form_class = PrintRegisterForm

    # This method is called when the data inserted in the form is valid
    def form_valid(self, form):
        # Saving with commit=False gets you a model object, then you can add your extra data and save it.
        printObject = form.save(commit=False)
        # Set the extra data
        printObject.qualification = 5
        printObject.responsible_user = self.request.user
        printObject.save()
        response = super(PrintRegister, self).form_valid(form)
        return response

    #  This method is called when the data inserted in the form is valid and saved
    def get_success_url(self):
        text_message = _(
            'Your print has been successfully registered.')
        messages.add_message(self.request, messages.SUCCESS, text_message)
        dev = reverse('printOrderManager:index_printManager')
        return dev
