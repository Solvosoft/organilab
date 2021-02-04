from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http.response import JsonResponse
from djgentelella.cruds.base import CRUDView
from msds.models import MSDSObject, OrganilabNode, RegulationDocument
from django.db.models.query_utils import Q
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _
from msds.forms import FormMSDSobject, FormMSDSobjectUpdate
from django.urls.base import reverse
from django.shortcuts import render
import zipfile
from django.conf import settings
import os


def index_msds(request):
    return render(request, 'index_msds.html')


def get_download_links(request, obj):

    new_url = reverse('msds:msds_msdsobject_detail', args=(obj.pk,))
    dev = '<a href="%s" target="_blank">%s</a>' % (
        new_url,
        _("Download"))
    if request.user.has_perm('msds.change_msdsobject'):
        new_url = reverse('msds:msds_msdsobject_update', args=(obj.pk,))
        dev += ' -- <a href="%s" target="_blank">%s</a>' % (
            new_url,
            _("Edit"))
    if request.user.has_perm('msds.delete_msdsobject'):
        new_url = reverse('msds:msds_msdsobject_delete', args=(obj.pk,))
        dev += ' -- <a href="%s" target="_blank">%s</a>' % (
            new_url,
            _("Delete"))
    return dev


def get_list_msds(request):
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
        objs = MSDSObject.objects.filter(
            Q(provider__icontains=q) | Q(product__icontains=q)
        ).order_by('product')
    else:
        objs = MSDSObject.objects.all().order_by('product')

    recordsFiltered = objs.count()
    p = Paginator(objs, length)
    if pgnum > p.num_pages:
        pgnum = 1
    page = p.page(pgnum)
    data = []
    for obj in page.object_list:
        data.append([
            obj.provider,
            obj.product,
            get_download_links(request, obj)
        ])

    dev = {
        "data": data,
        "recordsTotal": MSDSObject.objects.all().count(),
        "recordsFiltered": recordsFiltered
    }

    draw = request.GET.get('_', '')
    try:
        draw = int(draw)
        dev['draw'] = draw
    except:
        pass
    return JsonResponse(dev)


class MSDSObjectCRUD(CRUDView):
    model = MSDSObject
    views_available = ['create', 'update', 'detail', 'delete']
    namespace = "msds"
    add_form = FormMSDSobject
    update_form = FormMSDSobjectUpdate
    check_login = False
    check_perms = False
    perms = { 
        'create': ['msds.add_msdsobject'],
        'list': [],
        'delete': ['msds.delete_msdsobject'],
        'update': ['msds.update_msdsobject'],
        'detail': []
    }
    form_widget_exclude = ['file']

    def decorator_update(self, viewclass):
        return login_required(viewclass)

    def decorator_delete(self, viewclass):
        return login_required(viewclass)

    def get_create_view(self):
        CreateViewClass = super(MSDSObjectCRUD, self).get_create_view()

        class OCreateView(CreateViewClass):
            def get_success_url(self):
                url = reverse("msds:index_msds")
                messages.success(self.request,
                                 _("Your MSDS was uploaded successfully"))
                return url
        return OCreateView

    def get_update_view(self):
        EditViewClass = super(MSDSObjectCRUD, self).get_update_view()

        class OEditView(EditViewClass):

            def get_success_url(self):
                url = reverse("msds:index_msds")
                messages.success(self.request,
                                 _("Your MSDS was updated successfully"))
                return url

        return OEditView

    def get_delete_view(self):
        ODeleteClass = super(MSDSObjectCRUD, self).get_delete_view()

        class ODeleteView(ODeleteClass):

            def get_success_url(self):
                url = reverse("msds:index_msds")
                messages.success(self.request,
                                 _("Your MSDS was delete successfully"))
                return url

            def get_queryset(self):
                query = super(ODeleteView, self).get_queryset()
                if not self.request.user.has_perm('msds.delete_msdsobject'):
                    query = query.none()
                return query
        return ODeleteView


def organilab_tree_frame(request):  
    context = {}
    context['sections'] = OrganilabNode.objects.all()
    return render(request, 'msds/organilab_tree_frame.html', context)


def organilab_tree(request):
    content = request.GET.get('content', '')
    if content:
        return organilab_tree_frame(request)
    return render(request, 'msds/organilab_tree.html')


def regulation_view(request):
    regulations = RegulationDocument.objects.all()
    return render(request, 'regulation/regulations_document.html', {'object_list': regulations})


def get_name(name, country, path):
    ext = path.split('.')[-1]
    return "%s_%s.%s"%(name, country, ext)

def download_all_regulations(request):
    response = HttpResponse(content_type='application/force-download')
    z = zipfile.ZipFile(response, "w")
    regulations = RegulationDocument.objects.all()
    for doc in regulations:
        doc.file.open('rb')
        name = get_name(doc.name, doc.country, doc.file.url)
        z.write(os.path.join(settings.MEDIA_ROOT, doc.file.path), name)
    for file in z.filelist:
        file.create_system = 0
    z.close()
    response['Content-Disposition'] = 'attachment; filename="regulations.zip"'
    return response