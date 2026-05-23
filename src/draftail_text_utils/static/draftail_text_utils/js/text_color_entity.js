/**
 * Text color entity for Draftail.
 * Registers an entity type (TEXT_COLOR) that stores an arbitrary text color.
 * The entity is applied by `text-color` control when a custom text color is entered.
 * See:`src/draftail_text_utils/static/draftail_text_utils/js/text_color.js`
 */
(function () {
  const React = window.React;
  const ENTITY_TYPE = 'TEXT_COLOR';
  const STYLE_KEY = 'style';
  const DATASET_KEY = 'data-entity-type';

  // Decorator: renders the entity's text inline in the editor
  const TextColorDecorator = ({ children, contentState, entityKey }) => {
    const entity = contentState.getEntity(entityKey);
    const { color: entityColor } = entity.getData();
    if (!entityColor) return children;

    const color = entityColor == 'transparent' ? '#00000000' : entityColor;
    return React.createElement(
      'span',
      {
        [STYLE_KEY]: { color },
        [DATASET_KEY]: ENTITY_TYPE,
      },
      children,
    );
  };

  // Source: immediately closes (the control handles the UI)
  const TextColorSource = ({ onClose }) => {
    onClose();
    return null;
  };

  window.draftail.registerPlugin(
    {
      type: ENTITY_TYPE,
      source: TextColorSource,
      decorator: TextColorDecorator,
    },
    'entityTypes',
  );
})();
