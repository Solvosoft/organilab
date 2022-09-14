
const PanelComponent = Formio.Components.components.panel;

class CustomSection extends PanelComponent {
  constructor(...args) {
    super(...args);
  }

  static schema() {
    return PanelComponent.schema({
      type: 'custom_section',
      label: 'Section',
      key: 'Section',
      title: 'New Untitled Section',
    });
  }

  static get builderInfo() {
    return {
      title: 'Section',
      group: 'derb_layout',
      icon: 'list-alt',
      weight: 0,
      schema: CustomSection.schema()
    };
  }

  get defaultSchema() {
    return CustomSection.schema();
  }

  render() {
    return super.render();
  }

  attach(element) {
    return super.attach(element);
  }
}

CustomSection.editForm = function () {
  let editForm = PanelComponent.editForm([
    {
      key: 'conditional',
      label: 'Conditional Logic',
      components: [{
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
      }
      ]
    }
  ]);
  return editForm;
}

Formio.Components.addComponent('custom_section', CustomSection);
