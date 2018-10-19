'''
Created on 14 sep. 2018

@author: luisfelipe7
'''

from django.http.response import JsonResponse
from printOrderManager.models import PaperType, PrintObject, Contact
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
# Import for response
from django.http import HttpResponse
# Import JSON
import json
# Import for the reverse lazy, reverse, get_object_or_404 and redirect
from django.urls.base import reverse_lazy
from django.urls.base import reverse
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
# Import for django-guardian
from guardian.shortcuts import assign_perm
from guardian.shortcuts import remove_perm


def index_printOrderManager(request):
    return render(request, 'index_printOrderManager.html')

@login_required
def index_printManager(request):
    return render(request, 'index_printManager.html')

@login_required
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
        hola = 4
        user = User.objects.get(pk=obj.responsible_user_id)
        url = reverse('printOrderManager:index_printManageById', kwargs={'pk': obj.id})
        printActions = "<a  href="+url+"  class='btn btn-info'><span id='edit' class='glyphicon glyphicon-th-list' aria-hidden='true'></span>&nbsp; "+_('Manage')+"</a>&nbsp;"
                            # 1A. Define the onclick method
        printActions += "<a onclick='deletePrint(\"" + obj.name + "\" ,\"" + str(obj.id) + "\"  )' class='btn btn-danger'><span class='glyphicon glyphicon-remove' aria-hidden='true'></span>&nbsp; "+_('Delete')+"</a>"
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


# 4A. Delete print object by id and return a json with the result
@login_required
def delete_print_byId(request):
    if (request.META.get('HTTP_REFERER') is not None): # If the previous URL is None, redirect to the index page
        if (request.META.get('HTTP_REFERER') is not "http://localhost:8000/printOrderManager/index_printManager"): # If the previous URL is different of the index print manager, redirect to the index page
            response_data = {} # Create a JSON object
            if((request.GET.get('pk') is not None) and (request.GET.get('csrfmiddlewaretoken') is not None)): #If the pk or the csrf is says don't have permissions
                # Delete the print object
                try:
                    pk = int(request.GET.get('pk'))
                    instance = PrintObject.objects.get(id=pk)
                    instance.delete()
                    response_data['status'] = '0'
                    response_data['msg'] = 'The print '+str(request.GET.get('nombre'))+' was deleted successfully'
                    return HttpResponse(json.dumps(response_data),content_type="application/json")
                except PrintObject.DoesNotExist:
                    response_data['status'] = '1'
                    response_data['msg'] = 'The print '+str(request.GET.get('nombre'))+' was deleted by another user'
                    return HttpResponse(json.dumps(response_data),content_type="application/json")
            else:
                # Create a message for the error
                response_data['status'] = '2' # { 'msg': 'Post was deleted'}
                response_data['msg'] = 'You don\'t have permissions to delete a print' # { 'msg': 'Post was deleted'}    response_data[]
                return HttpResponse(json.dumps(response_data),content_type="application/json")
        else:
            # Redirect to other site
            return redirect('printOrderManager:index_printOrderManager')
    else:
        # Redirect to other site
        return redirect('printOrderManager:index_printOrderManager')

# PRINT MANAGER 

# Enter to the Print Manager (SB Admin 2: https://startbootstrap.com/template-overviews/sb-admin-2/) 
@login_required
def index_printManageById(request, pk):
    printObject = get_object_or_404(PrintObject, pk=pk)
    return render(request, 'printManageById/index_printManageById.html', {
            'printObject': printObject,  # Parametros enviados con la vista.
        })

# Give or drop permissions to a user
@login_required
def giveDropPermissionsById(request):
    if (request.META.get('HTTP_REFERER') is not None): # If the previous URL is None, redirect to the index page
        if (request.META.get('HTTP_REFERER') is not "http://localhost:8000/printOrderManager/contacts_printManageById/"+str(request.GET.get('pk'))): # If the previous URL is different of the index print manager, redirect to the index page
            response_data = {} # Create a JSON object
            if((request.GET.get('pk') is not None) and (request.GET.get('userID') is not None) and (request.GET.get('permissionType') is not None) and (request.GET.get('action') is not None)): #If the pk or the csrf is says don't have permissions
                # Obtain the permission
                permission = nameOfThePermission(str(request.GET.get('permissionType')))
                # Give or drop the permission to the user
                user = get_object_or_404(User, pk=int(request.GET.get('userID')))
                print = get_object_or_404(PrintObject, pk=int(request.GET.get('pk')))
                if (str(request.GET.get('action')) == "true"): # Otorgar Permisos
                    if (user.has_perm(permission, print)):
                        response_data['msg'] = '&nbsp; The user already has permission to edit the '+messageOfThePermission(str(request.GET.get('permissionType'))) # { 'msg': 'Post was deleted'}    response_data[]
                        response_data['status'] = '1'
                    else:
                        response_data['msg'] = '&nbsp; Permission to edit the '+messageOfThePermission(str(request.GET.get('permissionType')))+' has been assigned' # { 'msg': 'Post was deleted'}    response_data[]
                        assign_perm(permission, user, print)
                        response_data['status'] = '0'
                else: # Quitar Permisos
                    if (user.has_perm(permission, print)):
                        response_data['msg'] = '&nbsp; Permission to edit the '+messageOfThePermission(str(request.GET.get('permissionType')))+' has been removed' # { 'msg': 'Post was deleted'}    response_data[]
                        remove_perm(permission, user, print)
                        response_data['status'] = '0'
                    else:
                        response_data['msg'] = '&nbsp; The user already hasn\'t permission to edit the '+messageOfThePermission(str(request.GET.get('permissionType'))) # { 'msg': 'Post was deleted'}    response_data[]
                        response_data['status'] = '1'
                return HttpResponse(json.dumps(response_data),content_type="application/json")
            else:
                # Create a message for the error
                response_data['status'] = '2' # { 'msg': 'Post was deleted'}
                response_data['msg'] = '&nbsp; More data is necessary for manage the permissions' # { 'msg': 'Post was deleted'}    response_data[]
                return HttpResponse(json.dumps(response_data),content_type="application/json")
        else:
            # Redirect to other site
            return redirect('printOrderManager:index_printManager')
    else:
        # Redirect to other site
        return redirect('printOrderManager:index_printManager')


# Method that return the name of the permission depending of the param
def nameOfThePermission(permissionType):
    if (permissionType == 'i'):
        return 'changeInformation_printObject'
    elif (permissionType == 'c'):
        return 'changeContacts_printObject'
    elif (permissionType == 'p'):
        return 'changePaper_printObject'
    elif (permissionType == 's'):
        return 'changeSchedules_printObject'
    elif (permissionType == 'a'):
        return 'changeAdvertisements_printObject'


# Method that return the message of the permission depending of the param
def messageOfThePermission(permissionType):
    if (permissionType == 'i'):
        return 'information'
    elif (permissionType == 'c'):
        return 'contacts'
    elif (permissionType == 'p'):
        return 'paper types'
    elif (permissionType == 's'):
        return 'schedules'
    elif (permissionType == 'a'):
        return 'advertisements'

# Enter to the section of Contacts on the Print Manager
@login_required
def contacts_printManageById(request, pk):
    printObject = get_object_or_404(PrintObject, pk=pk)
    return render(request, 'printManageById/contacts_printManageById.html', {
            'printObject': printObject,  # Parametros enviados con la vista.
    })

# Return the contacts of an specific print
@login_required
def get_list_contactByPrint(request):
    q = request.GET.get('search[value]')
    length = request.GET.get('length', '10')
    pgnum = request.GET.get('start', '0')
    printObject = PrintObject.objects.get(pk=int(request.GET.get('pk')))

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
        printObject = PrintObject.objects.get(pk=int(request.GET.get('pk')))
        objs = printObject.contacts.all()

    recordsFiltered = objs.count()
    p = Paginator(objs, length)
    if pgnum > p.num_pages:
        pgnum = 1
    page = p.page(pgnum)
    data = []
    cont = 0
    permissions = "<script src='https://gitcdn.github.io/bootstrap-toggle/2.2.2/js/bootstrap-toggle.min.js'></script>"
    for obj in page.object_list:
        user = User.objects.get(pk=int(obj.assigned_user_id))
        if (cont == 0):
            symbol = 'class="fas fa-info-circle"'
            symbolPermission = 'i'
            if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
                permissions += "<input checked id='i"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
            else:
                permissions += "<input checked id='i"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
            cont += 1
        else:
            permissions = ""
            symbolPermission = 'i'
            symbol = 'class="fas fa-info-circle"'
            if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
                permissions += "<input checked id='i"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
            else:
                permissions += "<input checked id='i"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
            
        symbol = 'class="fas fa-users"'
        symbolPermission = 'c'
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input checked id='c"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input id='c"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"  
        
        symbol = 'class="fas fa-paper-plane"'
        symbolPermission = 'p'
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input checked id='p"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input id='p"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"  
        
        symbol = 'class="fas fa-calendar-alt"'
        symbolPermission = 's'
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input checked id='s"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input id='s"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"  
        
        symbol = 'class="fas fa-bell"'
        symbolPermission = 'a'
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input checked id='a"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input id='a"+str(user.id)+"' data-off='<i "+symbol+"></i>' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='<i "+symbol+"></i>' data-onstyle='primary'>&nbsp;"  
        
        data.append([
            user.username,
            user.first_name+" "+user.last_name,
            permissions,
        ])
    dev = {
        "data": data,
        "recordsTotal": objs.count(),
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
