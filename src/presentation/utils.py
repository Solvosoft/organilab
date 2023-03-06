import base64

import qrcode
import io

from django.contrib.contenttypes.models import ContentType
from presentation.models import QRModel


def build_qr_instance(url, object, organization):

    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    file = io.BytesIO()
    img.save(file)
    file.seek(0)
    img_svg = file.getvalue()
    b64_image=base64.b64encode(img_svg).decode()

    return QRModel.objects.create(qr_url=url,
                                  organization_id=organization,
                                  b64_image=b64_image,
                                  qr_image=img_svg.decode(), content_object=object)


def update_qr_instance(url, object, organization):
    cc_filters={
        'content_type__app_label': object._meta.app_label,
        'content_type__model': object._meta.model_name,
        'object_id': object.pk,
        'organization': organization

    }
    if not QRModel.objects.filter(**cc_filters).exists():
        return build_qr_instance(url, object, organization)

    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    file = io.BytesIO()
    img.save(file)
    file.seek(0)
    img_svg = file.getvalue()
    b64_image=base64.b64encode(img_svg).decode()
    return QRModel.objects.filter(**cc_filters).update(qr_url=url, b64_image=b64_image, qr_image=img_svg.decode())


def get_qr_by_instance(object, organization):
    ct=ContentType.objects.get_for_model(object)
    return QRModel.objects.filter(content_type=ct, organization=organization, object_id=object.pk).last()