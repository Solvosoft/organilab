const SelectComponent = Formio.Components.components.select;


class CustomSelect extends SelectComponent {
  constructor(...args) {
    super(...args);
  }

  static schema() {
    return SelectComponent.schema({
      type: 'custom_select',
      label: 'Select',
      key: 'Select',
      title: 'New Untitled Select',
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

  attach(element) {
    return super.attach(element);
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
  ]);
  console.log(editForm);
  return editForm;
}
Formio.Components.addComponent('custom_select', CustomSelect);