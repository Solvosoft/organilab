import base64

import qrcode
import io

from django.contrib.contenttypes.models import ContentType
from presentation.models import QRModel


def build_qr_instance(url, object):

    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    file = io.BytesIO()
    img.save(file)
    file.seek(0)
    img_svg = file.getvalue()
    b64_image=base64.b64encode(img_svg).decode()

    return QRModel.objects.create(qr_url=url,
                                  b64_image=b64_image,
                                  qr_image=img_svg.decode(), content_object=object)


def get_qr_by_instance(object):
    ct=ContentType.objects.get_for_model(object)
    return QRModel.objects.filter(content_type=ct, object_id=object.pk).last()