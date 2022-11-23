import time

from django.core.management import BaseCommand
import requests
from django.core.files.base import ContentFile

from sga.models import Pictogram


class Command(BaseCommand):
    help = 'Load Pictograms'

    def get_pictogram(self, url):
        name = url.split('/')[-1]
        print(name)

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'
        }
        response = requests.get(url, headers=headers)
        return ContentFile(response.content, name=name)


    def handle(self, *args, **options):
        pictograms =[
            {
                'name': 'GHS01 -Bomba Explotando - Explosivo',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/4/4a/GHS-pictogram-explos.svg')
            },
            {
                'name': 'GHS02 -Llama - Inflamable',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/6/6d/GHS-pictogram-flamme.svg')
            },
            {
                'name': 'GHS03 -Llama sobre círculo - Oxidante',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/e/e5/GHS-pictogram-rondflam.svg')
            },
            {
                'name': 'GHS04 -Botella de Gas - Gas Presurizado',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/6/6a/GHS-pictogram-bottle.svg')
            },
            {
                'name': 'GHS05 -Corrosión - Corrosivo.',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/a/a1/GHS-pictogram-acid.svg')
            },
            {
                'name': 'GHS06 -Calavera y Tibias Cruzadas - Veneno o peligro de muerte.',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/5/58/GHS-pictogram-skull.svg')
            },
            {
                'name': 'GHS07 -Signo de Exclamación - Irritante. ',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/c/c3/GHS-pictogram-exclam.svg')
            },
            {
                'name': 'GHS08 -Pecho agrietado - Peligro para la Salud, Mutagénico, Cancerígeno, Reprotóxico',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/2/21/GHS-pictogram-silhouette.svg')
            },
            {
                'name': 'GHS09 -Medio Ambiente - Dañino para el ambiente.',
                'image': self.get_pictogram(
                    'https://upload.wikimedia.org/wikipedia/commons/b/b9/GHS-pictogram-pollu.svg')
            },
        ]

        for pictogram in pictograms:
            Pictogram.objects.create(**pictogram)