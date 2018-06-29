from django.http.response import JsonResponse
from msds.models import MSDSObject
from django.conf import settings
from django.db.models.query_utils import Q
from django.core.paginator import Paginator
from django.utils.translation import ugettext as _


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
            '<a href="%s%s" target="_blank">%s</a>' % (
                settings.STATIC_URL,
                obj.file,
                _("Download"))
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
