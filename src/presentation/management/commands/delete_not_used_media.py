import pathlib
import shutil

from django.core.management import BaseCommand
from django.conf import settings
from django.apps import apps
from django.db.models import FileField, ImageField
import os

class Command(BaseCommand):

    def get_current_files(self):
        uploaders=[]
        files=[]
        for app in apps.all_models.keys():
            for model, klass in apps.all_models[app].items():
                fields = klass._meta.get_fields()
                for field in fields:
                    if isinstance(field, (FileField,ImageField)):
                        uploaders.append((field.name, klass))
                        files+=list(klass.objects.all().values_list(field.name, flat=True))
        return list(set(files))

    def move(self, oldpath, newpath):
        folder=pathlib.Path(newpath).parent
        if not folder.exists():
            folder.mkdir(exist_ok=True, parents=True)
        print(oldpath, newpath)
        shutil.move(oldpath, newpath)

    def handle(self, *args, **options):
        print(settings.MEDIA_ROOT)
        print(settings.QUARANTINE_FOLDER)
        if not os.path.exists(settings.QUARANTINE_FOLDER):
            os.mkdir(settings.QUARANTINE_FOLDER)
        path = settings.MEDIA_ROOT
        new_path=settings.QUARANTINE_FOLDER
        files = self.get_current_files()
        for root, dir_names, file_names in os.walk(path):
            for f in file_names:
                name = str(os.path.join(root, f)).replace(path, '')
                if name[0]=='/':
                    name=name[1:]
                if name not in files:
                    self.move(
                        os.path.join(root, f),
                        os.path.join(new_path, name)
                    )
        #print(set(files))
