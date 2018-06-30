from django.http.response import JsonResponse
from msds.models import MSDSObject
from django.db.models.query_utils import Q
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _
from cruds_adminlte.crud import CRUDView
from msds.forms import FormMSDSobject, FormMSDSobjectUpdate
from django.urls.base import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def get_download_links(request, obj):

    new_url = reverse('msds:msds_msdsobject_detail', args=(obj.pk,))
    dev = '<a href="%s" target="_blank">%s</a>' % (
        new_url,
        _("Download"))
    if request.user.has_perm('msds.add_msdsobject'):
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

    def decorator_update(self, viewclass):
        return login_required(viewclass)

    def decorator_delete(self, viewclass):
        return login_required(viewclass)

    def get_create_view(self):
        CreateViewClass = super(MSDSObjectCRUD, self).get_create_view()

        class OCreateView(CreateViewClass):
            def get_success_url(self):
                url = reverse("laboratory:index")
                messages.success(self.request,
                                 _("Your MSDS was uploaded successfully"))
                return url
        return OCreateView

    def get_update_view(self):
        EditViewClass = super(MSDSObjectCRUD, self).get_update_view()

        class OEditView(EditViewClass):

            def get_success_url(self):
                url = reverse("laboratory:index")
                messages.success(self.request,
                                 _("Your MSDS was updated successfully"))
                return url

        return OEditView

    def get_delete_view(self):
        ODeleteClass = super(MSDSObjectCRUD, self).get_delete_view()

        class ODeleteView(ODeleteClass):

            def get_success_url(self):
                url = reverse("laboratory:index")
                messages.success(self.request,
                                 _("Your MSDS was delete successfully"))
                return url

            def get_queryset(self):
                query = super(ODeleteView, self).get_queryset()
                if not self.request.user.has_perm('msds.delete_msdsobject'):
                    query = query.none()
                return query
        return ODeleteView
