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
    insert_object_data(data.object, tbody_instance)
    load_features(data.object['object_features'], tbody_instance)
    if (data.object['substance_characteristics']){
        manage_substance_characteristics(data.object['substance_characteristics'], tbody_instance)
    }
}
/*
Method that creates the substance characteristics
I: data (JSON), inst(Instance of HTML to append to)
O: None
*/
function manage_substance_characteristics(data, inst){
    let characteristics = define_usable_keys_detail(data)
    data = change_boolean_to_affirmation(data)
    insert_substance_data(data, inst, characteristics)
    append_characteristics_lists(data, inst)
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
Method that creates the iterable data if there is data to show
I: data (JSON), inst(Instance of HTML to append to)
O: None
*/

function append_characteristics_lists(data, inst){
    let characteristics_lists = {
        'white_organ': gettext('White Organs'),
        'h_code': gettext('H Codes'),
        'ue_code': gettext('UE Codes'),
        'nfpa': gettext('NFPA Codes')
    }
    titles = Object.keys(characteristics_lists)
    titles.forEach( (title) => {
        if (data[title] > 0){
            let temp_html = load_array_data(data[title], characteristics_lists[title])
            inst.append(temp_html)
        }
    })
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
Method that creates the features if there is any to show
I: data (JSON), inst(Instance of HTML to append to)
O: None
*/
function load_features(features, inst){
    let html_object = ""
    if (features.length > 0){
        for (feature of features){
            html_object += `<li> ${feature.name}</li>`
        }
        let features_html = `<tr><td class="shelfobject_titles">${gettext('Features')}</td><td>
            <ul class="shelfobjectfeatures shelfobject_list_elem">${html_object}</ul></td></tr>`
        inst.append(features_html)
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
Method that inserts all the characteristics inside characteristics which contains the usable keys
I: data (JSON), inst(Instance of HTML to append to)
O: None
*/
function insert_object_data(data, inst){
    let html_object = ''
    let object_titles = {
        'code': gettext('Code'),
        'name': gettext('Name'),
        'synonym': gettext('Synonym'),
        'description': gettext('Description'),
        'unit': gettext('Unit'),
        'model': gettext('Model'),
        'serie': gettext('Serie'),
        'plaque': gettext('Plaque')
    }
    titles = Object.keys(object_titles)
    titles.forEach( (title) => {
        let value = title == 'unit' ? data[title] : data.object_inst[title]
        html_object += `<tr><td class="shelfobject_titles">${object_titles[title]}</td>
        <td> ${value ? value : ""} </td></tr>`
    })
    inst.prepend(html_object)
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
I: array_list (Array), title(String)
O: None
*/
function load_array_data(array_list, title){
    let html_object = ""
    array_list.forEach((item) => html_object += `<li> ${item}</li>`)
    let html_section = `<tr><td class="shelfobject_titles">${title}</td><td>
        <ul class="shelfobject_list_elem">${html_object}</ul></td></tr>`
    return html_section

}