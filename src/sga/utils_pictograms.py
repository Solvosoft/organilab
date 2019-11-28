def ubic_pictograms(objects, pictograms, cant_objects):
    static_pict = 4
    obj_json_ind = 1
    ind_image = {}
    ind_image_tmp = []
    ind_pict_list = []

    for key, value in pictograms.items():
        ind_pict_list.append(key)

    while obj_json_ind != cant_objects and static_pict:
        attribute = objects[obj_json_ind].split(",")
        steps = 0
        for elem_a in attribute:
            if "type" in elem_a:
                if "image" in elem_a:
                    steps = 1
                else:
                    break
            elif steps == 1 and "src" in elem_a:
                url_begging = elem_a.split(":", 1)[1]
                url_end = url_begging.split("/")[-1][:-1]
                if "example" in url_end:
                    ind_image_tmp += [obj_json_ind]
                else:
                    static_pict -= 1
                    if url_end in ind_pict_list:
                        ind_pict_list.remove(url_end)
                break
        obj_json_ind += 1
    max_pic = min(static_pict, len(ind_pict_list), len(ind_image_tmp))
    total_img_add = list(range(max_pic))
    for ind_example_gif in total_img_add:
        url_pict = "/static/sga/img/pictograms/"
        pos_pict = ind_pict_list[ind_example_gif]
        url_pict += pictograms[pos_pict].name
        ind_image.update({ind_image_tmp.pop(0): url_pict})

    return ind_image, ind_image_tmp


def pic_selected(representation, pictograms):
    end_representation = ""
    objects = representation.split("},{")
    size_obj = len(objects)
    dict_image, image_delete = ubic_pictograms(objects, pictograms, size_obj)
    image_delete = image_delete[::-1]
    if image_delete:
        if image_delete[0] == size_obj - 1:
            end_representation = "}]," + objects[-1].split(",")[-1]
    for key, value in dict_image.items():
        objects[key] = objects[key].replace("/static/sga/img/pictograms/example.gif",
                                            value, 1)

    for pict_to_delete in image_delete:
        objects.pop(pict_to_delete)

    representation = "},{".join(x for x in objects)
    representation += end_representation
    return representation
