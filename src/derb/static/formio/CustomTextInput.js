const TextFieldComponent = Formio.Components.components.textfield;


class CustomTextInput extends TextFieldComponent {
  constructor(...args) {
    super(...args);
  }

  static schema() {
    return TextFieldComponent.schema({
      type: 'custom_textinput',
      label: 'Text Input',
      key: 'Text Input',
      title: 'New Untitled Text Input',
    });
  }

  static get builderInfo() {
    return {
      title: 'Text Input',
      group: 'derb_layout',
      icon: 'terminal',
      weight: 0,
      schema: CustomTextInput.schema()
    };
  }

  get defaultSchema() {
    return CustomTextInput.schema();
  }

  render() {
    return super.render();
  }

  attach(element) {
    return super.attach(element);
  }
}

CustomTextInput.editForm = function () {
  let editForm = TextFieldComponent.editForm([
    {
      key: 'conditional',
      label: 'Conditional Logic',
      components: [
          {
            key: 'simple-conditional',
            ignore: true,
          },
          {
            key: 'customConditionalPanel',
            ignore: true
          },
          {
            key: 'conditional',
            label: 'Derb Validation',
            type: 'textarea',
            placeholder: 'Enter the JSON Derb Validation Logic Here',
            rows: 5
          },

      ]
    },
  ]);
  console.log(editForm);
  return editForm;
}
Formio.Components.addComponent('custom_textinput', CustomTextInput);