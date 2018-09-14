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
# from msds.forms import FormMSDSobject, FormMSDSobjectUpdate
from django.urls.base import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render


def index_print(request):
    return render(request, 'index_print.html')
