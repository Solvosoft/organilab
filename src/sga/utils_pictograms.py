import json
import os

from organilab import settings


def pic_selected(representation, pictograms, context):
    size_obj = len(pictograms)
    temp_picts = list(pictograms)
    index = 0
    var = settings.STATIC_URL
    repro = json.loads(representation)
    for obj in repro['objects']:
        if obj['type'] == 'image':
            if 'logogen.jpg' in obj['src']:
                obj['src'] = context['logo_url']
            if 'barcodegen.jpg' in obj['src']:
                obj['src'] = context['barcode_url']
            if 'example.gif' in obj['src']:
                if index < size_obj:
                    path_to_file = var + "sga/img/pictograms/"
                    obj['src'] = path_to_file + temp_picts[index]
                    index += 1
                else:
                    obj['src'] = ''
    return repro
