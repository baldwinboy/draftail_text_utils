/**
 * Highlight color entity for Draftail.
 * Registers an entity type (HIGHLIGHT_COLOR) that stores an arbitrary highlight color.
 * The entity is applied by `highlight-color` control when a custom highlight color is entered.
 * See:`src/draftail_text_utils/static/draftail_text_utils/js/highlight_color.js`
 */
(function () {
  const React = window.React;
  const ENTITY_TYPE = 'HIGHLIGHT_COLOR';
  const STYLE_KEY = 'style';
  const DATASET_KEY = 'data-entity-type';

  // Decorator: renders the entity's text inline in the editor
  const HighlightColorDecorator = ({ children, contentState, entityKey }) => {
    const entity = contentState.getEntity(entityKey);
    const { backgroundColor: entityColor } = entity.getData();
    if (!entityColor) return children;

    const backgroundColor =
      entityColor == 'transparent' ? '#00000000' : entityColor;
    return React.createElement(
      'span',
      {
        [STYLE_KEY]: { backgroundColor },
        [DATASET_KEY]: ENTITY_TYPE,
      },
      children,
    );
  };

  // Source: immediately closes (the control handles the UI)
  const HighlightColorSource = ({ onClose }) => {
    onClose();
    return null;
  };

  window.draftail.registerPlugin(
    {
      type: ENTITY_TYPE,
      source: HighlightColorSource,
      decorator: HighlightColorDecorator,
    },
    'entityTypes',
  );
})();
