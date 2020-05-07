def create_pictograms(apps, schema_editor):
    Pictogram = apps.get_model('sga', 'Pictogram')
    WarningWord = apps.get_model('sga', 'WarningWord')
    ww = WarningWord.objects.create(
        name='Sin palabra'
    )

    for pic in ["5-2red.gif",
                "acide8.gif",
                "acide.gif",
                "acid_red.gif",
                "Aquatic-pollut-red.gif",
                "blan-red.gif",
                "bleu4.gif",
                "Bomba explotando.gif",
                "bottle.gif",
                "exclam.gif",
                "Gas inflamable sga.gif",
                "Gas inflamable transporte.gif",
                "jaune5-1.gif",
                "rondflam.gif",
                "rouge3.gif",
                "silhouete.gif",
                "skull6.gif",
                "skull.gif",
                "stripes.gif",
                "Trans.e1.1.gif",
                "Trans.e1.2.gif",
                "Trans.e1.3.gif",
                "Trans.e1.4.gif",
                "Trans.e1.5.gif",
                "Trans.e1.6.gif"]:
        Pictogram.objects.create(name=pic, warning_word=ww)
