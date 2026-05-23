/**
 * Font size entity for Draftail.
 * Registers an entity type (FONT_SIZE) that stores an arbitrary font size.
 * The entity is applied by `font-size` control when a custom size is entered.
 * See:`src/draftail_text_utils/static/draftail_text_utils/js/font_family.js`
 */
(function () {
  const React = window.React;
  const ENTITY_TYPE = 'FONT_SIZE';
  const STYLE_KEY = 'style';
  const DATASET_KEY = 'data-entity-type';

  const FontSizeDecorator = ({ children, contentState, entityKey }) => {
    const entity = contentState.getEntity(entityKey);
    const { size: fontSize } = entity.getData();
    return React.createElement(
      'span',
      {
        [STYLE_KEY]: { fontSize },
        [DATASET_KEY]: ENTITY_TYPE,
      },
      children,
    );
  };

  // Source: immediately closes (the control handles the UI)
  const FontSizeSource = ({ onClose }) => {
    onClose();
    return null;
  };

  window.draftail.registerPlugin(
    {
      type: ENTITY_TYPE,
      source: FontSizeSource,
      decorator: FontSizeDecorator,
    },
    'entityTypes',
  );
})();
