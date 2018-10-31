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
from django.http import HttpResponse, HttpResponseRedirect
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
# Import for Django Rest Framework - Token
from rest_framework.authtoken.models import Token


# Method to display a page for the login section


class PrintLogin(FormView):
    template_name = 'loginRegister/loginPrint.html'
    form_class = PrintLoginForm


# Method with the form to register a print
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
        # Set all the permissions to the user
        assign_perm("changeInformation_printObject",
                    self.request.user, printObject)
        assign_perm("changeContacts_printObject",
                    self.request.user, printObject)
        assign_perm("changePaper_printObject", self.request.user, printObject)
        assign_perm("changeSchedules_printObject",
                    self.request.user, printObject)
        assign_perm("changeAdvertisements_printObject",
                    self.request.user, printObject)
        response = super(PrintRegister, self).form_valid(form)
        return response

    #  This method is called when the data inserted in the form is valid and saved
    def get_success_url(self):
        text_message = _(
            'MESSAGE1')
        messages.add_message(self.request, messages.SUCCESS, text_message)
        dev = reverse('printOrderManager:index_printManager')
        return dev


# Method that return the index page to select the administrator

def index_printOrderManager(request):
    return render(request, 'index_printOrderManager.html')

# Method that return the index page with the list of prints


@login_required
def index_printManager(request):
    return render(request, 'index_printManager.html')

# Method that return the list of prints


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
                                                Q(name__icontains=q) | Q(contacts__assigned_user__id=request.user.id) | Q(qualification__icontains=q) | Q(responsible_user__username__icontains=q) |
                                                Q(responsible_user__first_name__icontains=q) | Q(responsible_user__last_name__icontains=q), Q(responsible_user_id=request.user.id)).order_by('creation_date').distinct()
    else:
        objs = PrintObject.objects.all().filter(
            Q(responsible_user_id=request.user.id) | Q(
                contacts__assigned_user__id=request.user.id)
        ).order_by('creation_date').distinct()

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
        url = reverse('printOrderManager:index_printManageById',
                      kwargs={'pk': obj.id})
        printActions = "<div class='btn-group'><button type='button' class='btn btn-info  dropdown-toggle' data-toggle='dropdown' aria-haspopup='true' aria-expanded='false'>Actions &nbsp;<span class='caret'></span></button><ul class='dropdown-menu ' role='menu'>"
        printActions += "<li><a  href="+url + \
            " ><span id='edit' class='glyphicon glyphicon-th-list' aria-hidden='true'></span>&nbsp; " + \
            _('Manage')+"</a></li>"
        # 1A. Define the onclick method
        if(request.user.id == obj.responsible_user_id):
            printActions += "<li><a onclick='deletePrint(\"" + obj.name + "\" ,\"" + str(
                obj.id) + "\"  )' ><span class='glyphicon glyphicon-remove' aria-hidden='true'></span>&nbsp; "+_('Delete')+"</a></li></ul></div>"
        else:
            printActions += "</ul></div>"
        printLogo = "<img class='iconTable' src='http://localhost:8000/media/" + \
            obj.logo.name+"'> &nbsp;&nbsp; " + obj.name
        while cont < obj.qualification:
            qualification += "<i class='fas fa-star fa-1x colorStar'></i>&nbsp;"
            cont += 1
        cont = 0
        while cont < (5-obj.qualification):
            qualification += "<img class='iconTable' src='http://localhost:8000/static/images/whiteStar.png'>"
            cont += 1
        if(request.user.id == obj.responsible_user_id):
            responsibleUser = "<span class='label label-warning'>" + \
                _("Owner")+"</span>"
        else:
            if(user.first_name == ""):
                responsibleUser = user.username
            else:
                responsibleUser = user.first_name+" " + \
                    user.last_name+" (" + user.username+")"

        if(obj.state == ""):
            state = _("<span class='label label-success'>Available</span>")
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
        "recordsTotal": PrintObject.objects.all().filter(Q(responsible_user_id=request.user.id) | Q(contacts__assigned_user__id=request.user.id)).count(),
        "recordsFiltered": recordsFiltered
    }

    draw = request.GET.get('_', '')
    try:
        draw = int(draw)
        dev['draw'] = draw
    except:
        pass
    return JsonResponse(dev)

# Method to delet the print by the id send it by ajax
# 4A. Delete print object by id and return a json with the result


@login_required
def delete_print_byId(request):
    # If the previous URL is None, redirect to the index page
    if (request.META.get('HTTP_REFERER') is not None):
        # If the previous URL is different of the index print manager, redirect to the index page
        if (request.META.get('HTTP_REFERER') is not "http://localhost:8000/printOrderManager/index_printManager"):
            response_data = {}  # Create a JSON object
            # If the pk or the csrf is says don't have permissions
            if((request.GET.get('pk') is not None) and (request.GET.get('csrfmiddlewaretoken') is not None)):
                # Delete the print object
                try:
                    pk = int(request.GET.get('pk'))
                    instance = PrintObject.objects.get(id=pk)
                    instance.delete()
                    response_data['status'] = '0'
                    response_data['msg'] = 'The print ' + \
                        str(request.GET.get('nombre')) + \
                        ' was deleted successfully'
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
                except PrintObject.DoesNotExist:
                    response_data['status'] = '1'
                    response_data['msg'] = 'The print ' + \
                        str(request.GET.get('nombre')) + \
                        ' was deleted by another user'
                    return HttpResponse(json.dumps(response_data), content_type="application/json")
            else:
                # Create a message for the error
                response_data['status'] = '2'  # { 'msg': 'Post was deleted'}
                # { 'msg': 'Post was deleted'}    response_data[]
                response_data['msg'] = 'You don\'t have permissions to delete a print'
                return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            # Redirect to other site
            return redirect('printOrderManager:index_printOrderManager')
    else:
        # Redirect to other site
        return redirect('printOrderManager:index_printOrderManager')


# METHODS FOR THE PRINT MANAGER
# Enter to the Print Manager (SB Admin 2: https://startbootstrap.com/template-overviews/sb-admin-2/)
# Method to verify if the user is the owner of the print or is a contact


def have_permissions(printObject, userId):
    permission = False
    if ((printObject.responsible_user).id == userId):
        permission = True
        return permission
    else:
        contacts = printObject.contacts.all()
        try:
            user = contacts.get(assigned_user_id=userId)
            permission = True
            return permission
        except Contact.DoesNotExist:  # printOrderManager.models.DoesNotExist
            return permission


# Method to verify if the contact is enabled

def isEnabled_contact(printObject, userId):
    permission = False
    if ((printObject.responsible_user).id == userId):
        permission = True
        return permission
    else:
        contacts = printObject.contacts.all()
        try:
            user = contacts.get(assigned_user_id=userId)
            if(user.state == "Enabled"):
                permission = True
            else:
                permission = False
            return permission
        except Contact.DoesNotExist:  # printOrderManager.models.DoesNotExist
            return permission


# Method to display the index page of the Print Manager

@login_required
def index_printManageById(request, pk):
    user = None
    if request.user.is_authenticated():
        user = request.user
    printObject = get_object_or_404(PrintObject, pk=pk)
    if(have_permissions(printObject, user.id) is True):
        if(isEnabled_contact(printObject, user.id) is True):
            return render(request, 'printManageById/index_printManageById.html', {
                # Parametros enviados con la vista.
                'printObject': printObject,
                'user': user,
            })
        else:
            messages.add_message(request, messages.ERROR, _("MESSAGE3"))
            return HttpResponseRedirect(reverse('printOrderManager:index_printManager'))
    else:
        messages.add_message(request, messages.ERROR, _("MESSAGE2"))
        return HttpResponseRedirect(reverse('printOrderManager:index_printManager'))


# Method to give or drop permissions to a user


@login_required
def giveDropPermissionsById(request):
    # If the previous URL is None, redirect to the index page
    if (request.META.get('HTTP_REFERER') is not None):
        # If the previous URL is different of the index print manager, redirect to the index page
        if (request.META.get('HTTP_REFERER') is not "http://localhost:8000/printOrderManager/contacts_printManageById/"+str(request.GET.get('pk'))):
            response_data = {}  # Create a JSON object
            # If the pk or the csrf is says don't have permissions
            if((request.GET.get('pk') is not None) and (request.GET.get('userID') is not None) and (request.GET.get('permissionType') is not None) and (request.GET.get('action') is not None)):
                # Obtain the permission
                permission = nameOfThePermission(
                    str(request.GET.get('permissionType')))
                # Give or drop the permission to the user
                user = get_object_or_404(
                    User, pk=int(request.GET.get('userID')))
                print = get_object_or_404(
                    PrintObject, pk=int(request.GET.get('pk')))
                if (str(request.GET.get('action')) == "true"):  # Otorgar Permisos
                    if (user.has_perm(permission, print)):
                        response_data['msg'] = '&nbsp; The user already has permission to edit and add the '+messageOfThePermission(
                            str(request.GET.get('permissionType')))  # { 'msg': 'Post was deleted'}    response_data[]
                        response_data['status'] = '1'
                    else:
                        response_data['msg'] = '&nbsp; Permission to edit and add the '+messageOfThePermission(str(request.GET.get(
                            'permissionType')))+' has been assigned'  # { 'msg': 'Post was deleted'}    response_data[]
                        assign_perm(permission, user, print)
                        response_data['status'] = '0'
                else:  # Quitar Permisos
                    if (user.has_perm(permission, print)):
                        response_data['msg'] = '&nbsp; Permission to edit and add the '+messageOfThePermission(str(request.GET.get(
                            'permissionType')))+' has been removed'  # { 'msg': 'Post was deleted'}    response_data[]
                        remove_perm(permission, user, print)
                        response_data['status'] = '0'
                    else:
                        response_data['msg'] = '&nbsp; The user already hasn\'t permission to edit and add the '+messageOfThePermission(
                            str(request.GET.get('permissionType')))  # { 'msg': 'Post was deleted'}    response_data[]
                        response_data['status'] = '1'
                return HttpResponse(json.dumps(response_data), content_type="application/json")
            else:
                # Create a message for the error
                response_data['status'] = '2'  # { 'msg': 'Post was deleted'}
                # { 'msg': 'Post was deleted'}    response_data[]
                response_data['msg'] = '&nbsp; More data is necessary for manage the permissions'
                return HttpResponse(json.dumps(response_data), content_type="application/json")
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


# Method that enter to the section of Contacts on the Print Manager


@login_required
def contacts_printManageById(request, pk):
    user = None
    if request.user.is_authenticated():
        user = request.user
    printObject = get_object_or_404(PrintObject, pk=pk)
    if(have_permissions(printObject, user.id) is True):
        if(isEnabled_contact(printObject, user.id) is True):
            return render(request, 'printManageById/contacts_printManageById.html', {
                # Parametros enviados con la vista.
                'printObject': printObject,
                'user': user,
            })
        else:
            messages.add_message(request, messages.ERROR, _("MESSAGE3"))
            return HttpResponseRedirect(reverse('printOrderManager:index_printManager'))
    else:
        messages.add_message(request, messages.ERROR, _("MESSAGE2"))
        return HttpResponseRedirect(reverse('printOrderManager:index_printManager'))


# Method that return view to add contacts on the Print Manager


@login_required
def createContact_printManageById(request, pk):
    user = None
    if request.user.is_authenticated():
        user = request.user
    printObject = get_object_or_404(PrintObject, pk=pk)
    if(have_permissions(printObject, user.id) is True):
        if(isEnabled_contact(printObject, user.id) is True):
            return render(request, 'printManageById/createContact_printManageById.html', {
                # Parametros enviados con la vista.
                'printObject': printObject,
                'user': user,
            })
        else:
            messages.add_message(request, messages.ERROR, _("MESSAGE3"))
            return HttpResponseRedirect(reverse('printOrderManager:index_printManager'))
    else:
        messages.add_message(request, messages.ERROR, _("MESSAGE2"))
        return HttpResponseRedirect(reverse('printOrderManager:index_printManager'))


# Method that return the list of contacts of an specific print


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

    # Filter Section
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
        name = user.first_name+" "+user.last_name
        toggle = ""

        # Set disable the bootstrap toogle
        if(request.user.has_perm('changeContacts_printObject', printObject) is True):
            pass
        else:
            toggle = 'disabled'

        # Permissions Section
        if (cont == 0):
            cont += 1
        else:
            permissions = ""

        symbol = 'class="fas fa-info-circle"'
        symbolPermission = 'i'
        textInput = '<div data-toggle="tooltip" data-placement="top" title="' + \
            _('Information')+'"><i '+symbol+'></i></div> '
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input "+toggle+" checked id='i"+str(user.id)+"' data-off='"+textInput+"'   type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"'  data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input "+toggle+" id='i"+str(user.id)+"' data-off='"+textInput+"'  type='checkbox'  data-toggle='toggle' onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"'   data-onstyle='primary'>&nbsp;"

        symbol = 'class="fas fa-users"'
        symbolPermission = 'c'
        textInput = '<div data-toggle="tooltip" data-placement="top" title="' + \
            _('Contacts')+'"><i '+symbol+'></i></div> '
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input "+toggle+" checked id='c"+str(user.id)+"' data-off='"+textInput+"'  type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"'  data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input "+toggle+" id='c"+str(user.id)+"' data-off='"+textInput+"'  type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"'  data-onstyle='primary'>&nbsp;"

        symbol = 'class="fas fa-paper-plane"'
        symbolPermission = 'p'
        textInput = '<div data-toggle="tooltip" data-placement="top" title="' + \
            _('Paper Types')+'"><i '+symbol+'></i></div> '
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input "+toggle+" checked id='p"+str(user.id)+"'  data-off='"+textInput+"'   type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"'  data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input "+toggle+" id='p"+str(user.id)+"'  data-off='"+textInput+"'  type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"'   data-onstyle='primary'>&nbsp;"

        symbol = 'class="fas fa-calendar-alt"'
        symbolPermission = 's'
        textInput = '<div data-toggle="tooltip" data-placement="top" title="' + \
            _('Schedules')+'"><i '+symbol+'></i></div> '
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input "+toggle+" checked id='s"+str(user.id)+"' data-off='"+textInput+"'  type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"' data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input "+toggle+" id='s"+str(user.id)+"' data-off='"+textInput+"' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"' data-onstyle='primary'>&nbsp;"

        symbol = 'class="fas fa-bell"'
        symbolPermission = 'a'
        textInput = '<div data-toggle="tooltip" data-placement="top" title="' + \
            _('Advertisements')+'"><i '+symbol+'></i></div> '
        if(user.has_perm(nameOfThePermission(symbolPermission), printObject) is True):
            permissions += "<input "+toggle+" checked id='a"+str(user.id)+"'  data-off='"+textInput+"' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"' data-onstyle='primary'>&nbsp;"
        else:
            permissions += "<input "+toggle+" id='a"+str(user.id)+"' data-off='"+textInput+"' type='checkbox'  data-toggle='toggle'  onchange='permissionsUser(\"" + str(
                printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + str(symbolPermission) + "\" )'  data-size='small'  data-on='"+textInput+"' data-onstyle='primary'>&nbsp;"

        state = None
        actionState = None
        if(obj.state == "Enabled"):
            state = "<span class='label label-success'>Enabled</span>"
            actionState = "Disabled"
        else:
            state = "<span class='label label-default'>Disabled</span>"
            actionState = "Enabled"

        # Actions Section
        if(request.user.has_perm('changeContacts_printObject'), printObject is True):
            # 1A. Define the onclick method
            actions = "<div class='btn-group'><button type='button' class='btn btn-info  dropdown-toggle' data-toggle='dropdown' aria-haspopup='true' aria-expanded='false'>Actions &nbsp;<span class='caret'></span></button><ul class='dropdown-menu ' role='menu'>"
            actions += "<li><a  href='#' onclick='defineValuesForm(\"" + str(printObject.id) + "\" ,\"" + str(user.id) + "\" ,\"" + user.username + "\",\"" + name + "\" ,\"" + obj.state + "\",\"" + obj.phone + "\" ,\"" + str(obj.id) + "\" )' data-toggle='modal' data-target='#formUpdateContact'><span id='edit' class='fas fa-edit' aria-hidden='true' ></span>&nbsp; " + \
                _('Edit')+"</a></li>"
            # actions += "<li><a  href='#' ><span id='state' class='far fa-eye' aria-hidden='true'></span>&nbsp; " + \
            #    _(actionState)+"</a></li>"
            actions += "<li><a  href='#' onclick='deleteContact(\"" + str(obj.id) + "\" ,\"" + user.username + \
                "\"  )' ><span id='delete' class='fas fa-user-minus' aria-hidden='true'></span>&nbsp; " + \
                _('Delete')+"</a></li>"
            actions += "</ul></div>"
            # Data Section
            data.append([
                state,
                user.username,
                user.first_name+" "+user.last_name,
                permissions,
                actions,
            ])
        else:
            # Data Section
            data.append([
                obj.state,
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


# Method that return the list of users that are not related with the print

@login_required
def get_list_usersNotRelatedToPrint(request):
    q = request.GET.get('search[value]')
    length = request.GET.get('length', '10')
    pgnum = request.GET.get('start', '0')
    printObject = PrintObject.objects.get(pk=int(request.GET.get('pk')))
    listOfUsers = None

    try:
        length = int(length)
        pgnum = 1 + (int(pgnum) / length)
    except:
        length = 10
        pgnum = 1

    # Filter Section
    if q:
        listOfUsers = User.objects.all().filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(username__icontains=q).order_by('username'))
    else:
        listOfUsers = User.objects.all()

    # Get an specific Print Object acording with the pk
    printObject = PrintObject.objects.get(pk=int(request.GET.get('pk')))
    objs = printObject.contacts.all()  # Get all the contacts from a print
    # Return all the id from the objs, Flat True means that is a single value
    listOfId = objs.values_list('assigned_user_id', flat=True)
    for obj in listOfId:
        print("Obj "+str(obj))
    # Exclude from the Query Set the elements with the id on listOfId
    finalUserList = listOfUsers.exclude(id__in=listOfId).exclude(
        id=printObject.responsible_user.id)
    recordsFiltered = finalUserList.count()
    p = Paginator(finalUserList, length)
    if pgnum > p.num_pages:
        pgnum = 1
    page = p.page(pgnum)
    data = []
    cont = 0
    for userObject in page.object_list:
        name = userObject.first_name+" "+userObject.last_name
        action = "<button type='button' onclick='defineValuesForm(\"" + str(printObject.id) + "\" ,\"" + str(userObject.id) + "\" ,\"" + userObject.username + "\",\"" + \
            name + "\" )' class='btn btn-info btn-sm' data-toggle='modal' data-target='#formAddContact'><i class='fas fa-user-plus'></i>&nbsp; Add Contact</button>"
        # Data Section
        data.append([
            userObject.username,
            name,
            userObject.email,
            action,
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


# Method to create a CRUDView


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
