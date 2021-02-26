import json

from organilab import settings


def pic_selected(representation, pictograms, context):
    size_obj = len(pictograms)
    temp_picts = list(pictograms)
    index = 0
    var = settings.STATIC_URL
    repro = json.loads(representation)

    for obj in repro['objects']:
         if obj['type'] == 'image':
            if 'example.gif' in str(obj['src']):
                if index < size_obj:
                    path_to_file = var + "sga/img/pictograms/"
                    if 'Sin Pictograma' in temp_picts[index]:
                        obj['type'] = 'deleted'
                    else:
                        obj['src'] = path_to_file + temp_picts[index]
                    index += 1
                else:
                    obj['type'] = 'deleted'
            else:
                pass

    repro['objects']=[item for item in repro['objects'] if item['type']!='deleted']
    return repro
