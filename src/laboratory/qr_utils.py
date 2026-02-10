from django.urls import reverse

from presentation.models import QRModel
from presentation.utils import update_qr_instance


def get_or_create_qr_shelf_object(request, shelfobject, organization, laboratory):
    schema = request.scheme + "://"
    domain = schema + request.get_host()
    url = domain + reverse(
        "laboratory:rooms_list", kwargs={"org_pk": organization, "lab_pk": laboratory}
    )
    url = url + "?labroom=%d&furniture=%d&shelf=%d&shelfobject=%d" % (
        shelfobject.shelf.furniture.labroom.pk,
        shelfobject.shelf.furniture.pk,
        shelfobject.shelf.pk,
        shelfobject.pk,
    )
    qr = QRModel.objects.filter(
        qr_url=url,
        content_type__app_label=shelfobject._meta.app_label,
        object_id=shelfobject.id,
        organization=organization,
        content_type__model=shelfobject._meta.model_name,
    ).first()

    if not qr:
        qr = update_qr_instance(url, shelfobject, organization)
    return qr, url
