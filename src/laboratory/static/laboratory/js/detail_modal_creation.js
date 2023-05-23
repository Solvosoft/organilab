/*
Method that gets the data from the API Response and creates a modal with it
I: data (JSON)
O: None
*/
function configure_modal(data){
    const instance = $('#shelfobject_detail_modal_body')
    $('#detail_modal_container').on('hidden.bs.modal', function () {
        instance.html("")
        $('#detail_modalLabel').html("")
    })
    $('#detail_modalLabel').append(data.object['object_detail'])
    let content = '<table class="table table-striped"><tbody id="shelfobject_detail_tbody"></tbody></table>'
    instance.append(content)
    let tbody_instance = $('#shelfobject_detail_tbody')
    if(data['qr'] !== undefined){
        insert_qr(data['qr'], data['url'])
    }
    let object_titles = {
        'code': gettext('Code'),
        'name': gettext('Name'),
        'synonym': gettext('Synonym'),
        'description': gettext('Description'),
        'model': gettext('Model'),
        'serie': gettext('Serie'),
        'plaque': gettext('Plaque')
    }
    insert_substance_data(data.object.object_inst, tbody_instance, object_titles)
    insert_substance_data(data.object, tbody_instance, {'unit': gettext('Unit')})
    append_data_lists(data.object, {'object_features': gettext('Features')}, tbody_instance)
    if (data.object['substance_characteristics']){
        manage_substance_characteristics(data.object['substance_characteristics'], tbody_instance)
    }
}

/*
Method that inserts the QR Code in the modal, if there is one available
I: qr (b64 image), url(string)
O: None
*/
function insert_qr(qr, url){
    let qr_container = `<div class="form-group row qr_img">
        <img src="data:image/svg+xml;base64,${qr}" alt="${gettext('Download QR')}">
        </div>
        <div class="form-group row justify-content-center">
            <div class="col-5 text-center" style="margin-bottom: 5">
                <a href="${url}" class="btn btn-success">
                <i class="fa fa-download" ></i>
                ${gettext('Download QR')}</a>
            </div>
        </div>`
        $('#shelfobject_detail_modal_body').prepend(qr_container)
}

/*
Method that creates the substance characteristics
I: data (JSON), inst(Instance of HTML to append to)
O: None
*/
function manage_substance_characteristics(data, inst){
    let characteristics = define_usable_keys_detail(data)
    let characteristics_lists = {
        'white_organ': gettext('White Organs'),
        'h_code': gettext('H Codes'),
        'ue_code': gettext('UE Codes'),
        'nfpa': gettext('NFPA Codes')
    }
    data = change_boolean_to_affirmation(data)
    insert_substance_data(data, inst, characteristics)
    append_data_lists(data, characteristics_lists, inst)
    if (data['security_sheet']){
        let security_html = `<tr><td class="shelfobject_titles">${gettext('Security Sheet')}</td>
            <td><a href="${data['security_sheet']}" target="_blank"> ${gettext('Download')}</a></td></tr>`
        inst.append(security_html)
    }
    if(data['img_representation']){
        let image_rep_html = `<tr><td class="shelfobject_titles">${gettext('Sustance Representation')}</td>
            <img href="${data['img_representation']}" width="200px" height="200px" /></tr>`
        inst.append(image_rep_html)
    }
}

/*
Method that creates a dictionary with the necessary keys from the substance characteristics
I: data (JSON)
O: values (dict)
*/
function define_usable_keys_detail(data){
    let values = {
            'cas_id_number': gettext('Cas Number'),
            'is_precursor': gettext('Is Precursor'),

    }
    if (data['is_precursor']){
        values['precursor_type'] = gettext('Precursor Type')
    }
    values['iarc'] = gettext('IARC')
    values['imdg'] = gettext('IMDG')
    values['bioaccumulable'] = gettext('Bio Accumulable')
    values['seveso_list'] = gettext('Is Seveso list III?')
    values['molecular_formula'] = gettext('Molecular Formula')

    return values
}

/*
Method that changes the boolean value of some data to 'Yes' or 'No'
I: data (JSON)
O: data (JSON)
*/
function change_boolean_to_affirmation(data){
    let positive = gettext('Yes')
    let negative = gettext('No')
    data['is_precursor'] = data['is_precursor'] ? positive:negative
    data['seveso_list'] = data['seveso_list'] ? positive:negative
    data['molecular_formula'] = data['molecular_formula'] ? positive:negative
    data['bioaccumulable'] = data['molecular_formula'] ? positive:negative
    return data
}

/*
Method that creates the iterable data if there is data to show
I: data (JSON), inst(Instance of HTML to append to)
O: None
*/
function append_data_lists(data, data_lists, inst, nested_key){
    console.log(data_lists)
    titles = Object.keys(data_lists)
    titles.forEach( (title) => {
        if (data[title].length > 0){
            load_array_data(data[title], data_lists[title], inst, nested_key)
        }
    })
}

/*
Method that inserts all the substance data except for the ones containing arrays
I: data (JSON), inst(Instance of HTML to append to), object_titles (dict)
O: None
*/
function insert_substance_data(data, inst, object_titles){
    let html_object = ''
    titles = Object.keys(object_titles)
    titles.forEach( (title) => {
        let value = data[title]
        if(typeof value == 'object' && value){
            value = value.description
        }
        html_object += `<tr><td class="shelfobject_titles">${object_titles[title]}</td>
        <td> ${value ? value : ""} </td></tr>`
    })
    inst.append(html_object)
}

/*
Method that inserts all the substance characteristics that are arrays
I: array_list (Array), title(String), inst(Instance of HTML to append to)
O: None
*/
function load_array_data(array_list, title, inst){
    let html_object = ""
    let nested_key = Object.keys(array_list[0])[0]
    array_list.forEach((item) => {
        let value = item
        if (nested_key){
            value = value[nested_key]
        }
        html_object += `<li>${value}</li>`
    })
    let html_section = `<tr><td class="shelfobject_titles">${title}</td><td>
        <ul class="shelfobject_list_elem">${html_object}</ul></td></tr>`
    inst.append(html_section)
}