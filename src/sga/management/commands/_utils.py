def get_warning_word(WarningWord, name):
    instance, x = WarningWord.objects.get_or_create(name=name)
    return instance

def load_pictograms(WarningWord, Pictogram,get_pictogram,  PICTOGRAMS):
        pictograms =[
            {
                'name': 'GHS01 -Bomba Explotando - Explosivo',
                'warning_word': get_warning_word(WarningWord, 'Peligro'),
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/4/4a/GHS-pictogram-explos.svg')
            },
            {
                'name': 'GHS02 -Llama - Inflamable',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/6/6d/GHS-pictogram-flamme.svg')
            },
            {
                'name': 'GHS03 -Llama sobre círculo - Oxidante',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/e/e5/GHS-pictogram-rondflam.svg')
            },
            {
                'name': 'GHS04 -Botella de Gas - Gas Presurizado',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/6/6a/GHS-pictogram-bottle.svg')
            },
            {
                'name': 'GHS05 -Corrosión - Corrosivo',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/a/a1/GHS-pictogram-acid.svg')
            },
            {
                'name': 'GHS06 -Calavera y Tibias Cruzadas - Veneno o peligro de muerte',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/5/58/GHS-pictogram-skull.svg')
            },
            {
                'name': 'GHS07 -Signo de Exclamación - Irritante',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/c/c3/GHS-pictogram-exclam.svg')
            },
            {
                'name': 'GHS08 -Pecho agrietado - Peligro para la Salud, Mutagénico, Cancerígeno, Reprotóxico',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/2/21/GHS-pictogram-silhouette.svg')
            },
            {
                'name': 'GHS09 -Medio Ambiente - Dañino para el ambiente',
                'image': get_pictogram(Pictogram,
                    'https://upload.wikimedia.org/wikipedia/commons/b/b9/GHS-pictogram-pollu.svg')
            },
        ]


        for pictogram in pictograms:
            PICTOGRAMS[pictogram['name']]=Pictogram.objects.create(**pictogram)
