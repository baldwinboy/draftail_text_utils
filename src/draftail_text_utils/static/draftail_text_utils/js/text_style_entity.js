(function () {
  if (!window.draftail) return;

  var React = window.React;
  var ENTITY_TYPE = 'TEXT_STYLE';
  var STYLE_KEY = 'style';
  var DATASET_KEY = 'data-entity-type';

  var TextStyleDecorator = function (_ref) {
    var children = _ref.children;
    var contentState = _ref.contentState;
    var entityKey = _ref.entityKey;
    var entity;

    try {
      entity = contentState.getEntity(entityKey);
    } catch (e) {
      return children;
    }

    if (!entity) return children;

    var data = entity.getData() || {};
    var color = data.color;
    var backgroundColor = data.backgroundColor;
    var size = data.size;
    var linkUrl = data.url;
    var linkId = data.id;

    var style = {};
    if (color) style.color = color;
    if (backgroundColor) style.backgroundColor = backgroundColor;
    if (size) style.fontSize = typeof size === 'number' ? size + 'px' : size;

    var setStyleRef = function (el) {
      if (!el) return;
      if (color) el.style.setProperty('color', color, 'important');
      if (backgroundColor)
        el.style.setProperty('background-color', backgroundColor, 'important');
      if (size)
        el.style.setProperty(
          'font-size',
          typeof size === 'number' ? size + 'px' : size,
          'important',
        );
    };

    var hasLink = linkUrl || linkId !== undefined;

    if (hasLink) {
      var attrs = {
        href: linkUrl || '#',
        ref: setStyleRef,
        [STYLE_KEY]: style,
        [DATASET_KEY]: ENTITY_TYPE,
        className: 'StyledLink',
      };
      return React.createElement('a', attrs, children);
    }

    return React.createElement(
      'span',
      {
        ref: setStyleRef,
        [STYLE_KEY]: style,
        [DATASET_KEY]: ENTITY_TYPE,
      },
      children,
    );
  };

  var TextStyleSource = function (_ref2) {
    var onClose = _ref2.onClose;
    if (onClose) onClose();
    return null;
  };

  window.draftail.registerPlugin(
    {
      type: ENTITY_TYPE,
      source: TextStyleSource,
      decorator: TextStyleDecorator,
    },
    'entityTypes',
  );

  // Also provide a decorator for pre-existing LINK entities so they render
  // correctly in the editor even when no TEXT_STYLE entity is involved.
  // The source is preserved from styled_link_source.js's registration.
  window.draftail.registerPlugin(
    {
      type: 'LINK',
      source: window.draftail.StyledLinkSource,
      decorator: TextStyleDecorator,
    },
    'entityTypes',
  );
})();
