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
            refreshOn: 'data.api',
            conditional: {
              json: { '===': [{ var: 'dataSrc' }, 'api_org_structure'] },
            },
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
            tooltip: 'Select an option from the available APIs in Organilab',
            data: {
              values: [
                { label: 'Inform', value: 'api_inform' },
                { label: 'Incident Report', value: 'api_incident' },
                { label: 'Laboratory by User', value: 'api_laboratory_by_user' },
                { label: 'Laboratory by Organization', value: 'api_laboratory_by_org' },
                { label: 'Users in Lab/Organization', value: 'api_org_structure' },
                { label: 'Objects', value: 'api_objects' },
              ]
            },
            defaultValue: 'api_inform',
            weight: 2,
            onChange(context) {
                let route = window.location.pathname;
                let host = window.location.host;
                let org_pk = route.charAt(6)
                let view = context.instance.data.data.api
                view = view.replace('api_', '').replace('_by_user', '').replace('_by_org', 'Org')
                view = view.replace('_structure', '').replace('_', '').replace('incident', 'incidentReport')
                let schema = window.location.protocol + '/'
                let url = `${schema}/${host}/derb/${org_pk}/api/${view}View/`
                context.instance.data.data.url = url

            },
        },
      ]
    }
  ]);
  return editForm;
}

Formio.Components.addComponent('custom_select', CustomSelect);