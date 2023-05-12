const SelectComponent = Formio.Components.components.select;


class CustomSelect extends SelectComponent {
  constructor(...args) {
    super(...args);
  }

  static schema() {
    return SelectComponent.schema({
      type: 'custom_select',
      label: 'Select',
      key: 'custom_select',
      title: 'Custom API Select',
      idPath: 'item.key',
      template: '<option value={{item.key}}> {{item.value}} </option>',
      dataSrc: 'url',
      valueProperty: 'key',
      defaultValue: '',
      lazyLoad: false,
      dataType: 'number',
      data:{
        api: ''
      }
    });
  }

  static get builderInfo() {
    return {
      title: 'Select',
      group: 'derb_layout',
      icon: 'terminal',
      weight: 0,
      schema: SelectComponent.schema()
    };
  }

  get defaultSchema() {
    return CustomSelect.schema();
  }

  render() {
    return super.render();
  }

  detach() {
        return super.detach();
    }

  attach(element) {
    return super.attach(element);
  }

  destroy() {
    return super.destroy();
  }
}

CustomSelect.editForm = function () {
  let params = ''
  let editForm = SelectComponent.editForm([
    {
      key: 'conditional',
      ignore: true
    },
    {
        key: 'validation',
        ignore: true
    },
    {
        key: 'valueProperty',
        hidden: true
    },
    {
        key: 'api',
        ignore: true
    },
    {
        key: 'logic',
        ignore: true
    },
    {
        key: 'layout',
        ignore: true
    },
    {
      key: 'data',
      label: 'Data',
      components: [
        {
            key: 'multiple',
            weight: 10
        },
        {
            key: 'persistent',
            ignore: true
        },
        {
            key: 'protected',
            ignore: true
        },
        {
            key: 'template',
            ignore: true
        },
        {
            key: 'idPath',
            ignore: true,
        },
        {
            key: 'dataSrc',
            ignore: true
        },
        {
            key: 'data.url',
            refreshOn: 'data.api',
            ignore: true
        },
        {
            key: 'data.headers',
            ignore: true
        },
        {
            key: 'defaultValue',
            ignore: true
        },
        {
            key: 'lazyLoad',
            ignore: true
        },
        {
            key: 'selectValues',
            ignore: true
        },
        {
            key: 'dataType',
            ignore: true
        },
        {
            key: 'searchField',
            ignore: true
        },
        {
            key: 'refreshOn',
            ignore: true
        },
        {
            key: 'refreshOnBlur',
            ignore: true
        },
        {
            key: 'filter',
            ignore: true
        },
        {
            key: 'searchDebounce',
            ignore: true
        },
        {
            key: 'sort',
            ignore: true
        },
        {
            type: 'select',
            label: 'API',
            key: 'data.api',
            input: true,
            tooltip: gettext('Select an option from the available APIs in Organilab'),
            data: {
              values: [
                { label: gettext('Inform'), value: 'api_inform' },
                { label: gettext('Incident Report'), value: 'api_incident' },
                { label: gettext('Laboratory by User'), value: 'api_laboratory_by_user' },
                { label: gettext('Laboratory by Organization'), value: 'api_laboratory_by_org' },
                { label: gettext('Users in Lab/Organization'), value: 'api_org_structure' },
                { label: gettext('Objects'), value: 'api_objects' },
              ]
            },
            defaultValue: 'api_inform',
            weight: 1,
            onChange(context) {
                // The url for the preview is created
                let route = window.location.pathname.split('/');
                let host = window.location.host;
                let org_pk = route[2] // Organization ID
                let view = context.instance.data.data.api
                view = view.replace('api_', '').replace('_by_user', '').replace('_by_org', 'Org')
                view = view.replace('_structure', '').replace('_', '').replace('incident', 'incidentReport')
                let schema = window.location.protocol + '/'
                let url = `${schema}/${host}/derb/${org_pk}/api/${view}View/`
                context.instance.data.data.url = url
            },
        },
        {
            /*
            Optional setting that enables when a user selects api_org_structure
            Allows the user to give a Lab identifier for the preview, if none is given the search is done by organization
            */
            key: 'params',
            label: gettext('Laboratory identifier'),
            input: true,
            type: 'number',
            weight: 2,
            conditional: {
              json: { '===': [{ var: 'data.data.api' }, 'api_org_structure'] },
            },
            onChange(context) {
                //The parameter for users by laboratory is added or removed
                let temp_params = context.instance.data.params
                if (temp_params && temp_params > 0) {
                    context.instance.data.data.url += `?lab=${temp_params}`
                    params = `?lab=${temp_params}`
                }
                else{
                    let temp_url = context.instance.data.data.url
                    temp_url = temp_url.replace(params, '')
                    context.instance.data.data.url = temp_url
                    params = ''
                }
            }
        },
      ]
    }
  ]);
  return editForm;
}

Formio.Components.addComponent('custom_select', CustomSelect);