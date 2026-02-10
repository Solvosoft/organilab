import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.urls import reverse
import io
from laboratory.models import ShelfObject
from django.contrib.sites.models import Site


def generate_QR_img_file(url, file_name="qrcode", extension_file=".svg"):
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgImage)
    file = io.BytesIO()
    img.save(file)
    file.seek(0)
    content = ContentFile(file.getvalue(), name=file_name + extension_file)
    return content


class Command(BaseCommand):
    help = "Create QR"

    def handle(self, *args, **options):

        for shelfobject in ShelfObject.objects.all():
            laboratory = (
                shelfobject.shelf.furniture.labroom.laboratory_set.all().first()
            )
            if not laboratory:
                print(
                    "Laboratory: ",
                    shelfobject.pk,
                    str(shelfobject),
                    shelfobject.shelf.furniture.labroom,
                )
                continue
            org = laboratory.organization
            if not org:
                print(
                    "Orga:",
                    shelfobject.pk,
                    str(shelfobject),
                    shelfobject.shelf.furniture,
                )
                continue

            schema = "http%s://" % ("" if settings.DEBUG else "s",)
            domain = schema + Site.objects.all().first().domain
            url = domain + reverse(
                "laboratory:rooms_list",
                kwargs={"org_pk": org.pk, "lab_pk": laboratory.pk},
            )
            url = url + "#labroom=%d&furniture=%d&shelf=%d&shelfobject=%d" % (
                shelfobject.shelf.furniture.labroom.pk,
                shelfobject.shelf.furniture.pk,
                shelfobject.shelf.pk,
                shelfobject.pk,
            )

            shelfobject.shelf_object_url = url
            img = generate_QR_img_file(url, file_name="qrcode_%d" % (shelfobject.pk,))
            shelfobject.shelf_object_qr = img
            shelfobject.save()
