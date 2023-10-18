from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
import os
from django.conf import settings
from django.utils.text import slugify

from laboratory.models import (ShelfObject, SustanceCharacteristics, Protocol,
                               RegisterUserQR)
from msds.models import MSDSObject, RegulationDocument
from report.models import TaskReport
from risk_management.models import IncidentReport
from sga.models import DisplayLabel
from pathlib import Path


class Command(BaseCommand):

    help = 'Set media files names'

    def set_media_name(self, media):
        initial_path = media.path
        actual_name = media.name
        last_slash_index = 0
        path = Path(media.name)
        extension = path.suffix
        name = slugify(path.stem)

        if actual_name.find("/")>-1:
            last_slash_index = actual_name.rindex('/')

        new_name = actual_name[0:last_slash_index] + "/" + slugify(name)+extension
        new_path = settings.MEDIA_ROOT + new_name

        return [new_name,initial_path,new_path]

    def set_substance_img_representation(self):
        substances = SustanceCharacteristics.objects.all()

        for substance in substances:
            if substance.img_representation:

                name, initial_path, new_path = self.set_media_name(substance.img_representation)
                substance.img_representation.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    substance.save()

    def set_substance_security_sheet(self):
        substances = SustanceCharacteristics.objects.all()

        for substance in substances:

            if substance.security_sheet:
                name, initial_path, new_path = self.set_media_name(substance.security_sheet)
                substance.security_sheet.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    substance.save()
                    print(substance.security_sheet.url)
    def set_shelf_object_qr(self):
        shelfobjects = ShelfObject.objects.all()

        for shelfobject in shelfobjects:

            if shelfobject.shelf_object_qr:
                name, initial_path, new_path = self.set_media_name(shelfobject.shelf_object_qr)
                shelfobject.shelf_object_qr.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    shelfobject.save()
                    print(shelfobject.shelf_object_qr.url)

    def set_protocol_file(self):
        protocols = Protocol.objects.all()

        for protocol in protocols:

            if protocol.file:

                name, initial_path, new_path = self.set_media_name(protocol.file)
                protocol.file.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    protocol.save()
                    print(protocol.file.url)

    def set_register_user_qr(self):
        register_users = RegisterUserQR.objects.all()

        for register_user in register_users:
            if register_user.register_user_qr:

                name, initial_path, new_path = self.set_media_name(register_user.register_user_qr)
                register_user.register_user_qr.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    register_user.save()
                    print(register_user.register_user_qr)

    def set_msds_file(self):
        msdsobjects = MSDSObject.objects.all()

        for msds in msdsobjects:
            if msds.file:
                name, initial_path, new_path = self.set_media_name(msds.file)
                msds.file.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    msds.save()
                    print(msds.file)

    def set_regulation_document_file(self):
        regulation_docs = RegulationDocument.objects.all()

        for regulation_doc in regulation_docs:
            if regulation_doc.file:
                name, initial_path, new_path = self.set_media_name(regulation_doc.file)
                regulation_doc.file.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    regulation_doc.save()
                    print(regulation_doc.file.url)

    def set_task_report_file(self):
        taskreports = TaskReport.objects.all()

        for taskreport in taskreports:
            if taskreport.file:
                name, initial_path, new_path = self.set_media_name(taskreport.file)
                taskreport.file.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    taskreport.save()
                    print(taskreport.file.url)

    def set_incident_report_file(self):
        incident_reports = IncidentReport.objects.all()

        for incident_report in incident_reports:
            if incident_report.notification_copy:
                name, initial_path, new_path = self.set_media_name(incident_report.notification_copy)
                incident_report.notification_copy.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    incident_report.save()
                    print(incident_report.notification_copy.url)

    def set_display_label_logo(self):
        display_labels = DisplayLabel.objects.all()

        for display_label in display_labels:
            if display_label.logo:
                name, initial_path, new_path = self.set_media_name(display_label.logo)
                display_label.logo.name = name

                if default_storage.exists(initial_path):
                    os.rename(initial_path, new_path)
                    display_label.save()
                    print(display_label.logo.url)

    def handle(self, *args, **options):

        self.set_substance_security_sheet()
        self.set_substance_img_representation()
        self.set_shelf_object_qr()
        self.set_protocol_file()
        self.set_register_user_qr()
        self.set_msds_file()
        self.set_regulation_document_file()
        self.set_task_report_file()
        self.set_incident_report_file()
        self.set_display_label_logo()
