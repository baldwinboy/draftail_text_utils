(function () {
  if (!window.draftail) return;

  var React = window.React;
  var ToolbarButton = window.Draftail.ToolbarButton;
  var dt = window.DraftailTextUtils;
  var control = dt.parseControl('dynamic-link');
  var entityType = 'TEXT_STYLE';

  // Optional host-supplied context groups:
  //   window.draftailTextUtils.dynamicLinkContext = [
  //     {title, description, items: [{token, description}]}, ...
  //   ]
  function getContextGroups() {
    var data = window.draftailTextUtils || {};
    var groups = data.dynamicLinkContext;
    return Array.isArray(groups) ? groups : [];
  }

  var DynamicLinkControl = class DynamicLinkControl extends React.Component {
    constructor(props) {
      super(props);
      this.state = { isOpen: false, value: '' };
      this.controlRef = React.createRef();
    }

    componentDidMount() {
      document.addEventListener('mousedown', this.handleClickOutside);
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);
    }

    getActiveExpression() {
      return dt.getActiveEntityData(
        this.props.getEditorState(),
        entityType,
        'dynamic',
      );
    }

    toggleDropdown(force) {
      var willBeOpen = typeof force === 'boolean' ? force : !this.state.isOpen;
      if (willBeOpen && !this.state.isOpen) {
        dt.saveSelection(this.props.getEditorState);
      }
      this.setState({
        isOpen: willBeOpen,
        value: willBeOpen ? this.getActiveExpression() || '' : this.state.value,
      });
    }

    apply() {
      var expression = (this.state.value || '').trim();
      var editorState = dt.restoreSelection(this.props.getEditorState());
      if (expression) {
        editorState = dt.mergeStyleEntity(editorState, entityType, {
          dynamic: expression,
        });
      } else {
        editorState = dt.removeStyleProperty(
          editorState,
          entityType,
          'dynamic',
        );
      }
      this.props.onChange(editorState);
      this.setState({ isOpen: false });
    }

    remove() {
      var editorState = dt.restoreSelection(this.props.getEditorState());
      editorState = dt.removeStyleProperty(editorState, entityType, 'dynamic');
      this.props.onChange(editorState);
      this.setState({ isOpen: false });
    }

    handleClickOutside = (event) => {
      if (dt.clickOutsideGuard(this.controlRef, event)) {
        this.setState({ isOpen: false });
      }
    };

    handleChange = (e) => {
      this.setState({ value: e.target.value });
    };

    handleKeyDown = (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.apply();
      } else if (e.key === 'Escape') {
        this.toggleDropdown(false);
      }
    };

    insertToken = (token) => {
      if (token) {
        this.setState({ value: token });
      }
    };

    renderContextGroup = (group, index) => {
      var items = (group && group.items) || [];
      if (!items.length) return null;

      var summary = React.createElement(
        'summary',
        { className: 'Draftail--dynamic-link-summary' },
        group.title || 'Context values',
      );

      var list = React.createElement(
        'ul',
        { className: 'Draftail--dynamic-link-token-list' },
        items.map((item, itemIndex) =>
          React.createElement(
            'li',
            {
              key: `${index}-${itemIndex}`,
              className: 'Draftail--dynamic-link-token-item',
            },
            React.createElement(
              'button',
              {
                type: 'button',
                className: 'Draftail--dynamic-link-token',
                title: item.description || item.token,
                onClick: () => this.insertToken(item.token),
              },
              item.token,
            ),
            item.description
              ? React.createElement(
                  'span',
                  { className: 'Draftail--dynamic-link-token-desc' },
                  item.description,
                )
              : null,
          ),
        ),
      );

      return React.createElement(
        'details',
        {
          key: `DYNAMIC_LINK_GROUP_${index}`,
          className: 'Draftail--dynamic-link-group',
          open: index === 0,
        },
        summary,
        list,
      );
    };

    renderContextGroups() {
      var groups = getContextGroups();
      if (!groups.length) return null;
      var rendered = groups
        .map((group, index) => this.renderContextGroup(group, index))
        .filter(Boolean);
      if (!rendered.length) return null;
      return React.createElement(
        'div',
        { className: 'Draftail--dynamic-link-groups' },
        rendered,
      );
    }

    render() {
      var active = this.getActiveExpression();
      var icon = '#icon-' + control.icon;

      var input = React.createElement('input', {
        key: 'DYNAMIC_LINK_INPUT',
        type: 'text',
        className: 'Draftail--dynamic-link-input',
        placeholder: '{{ user.url }}',
        value: this.state.value,
        onChange: this.handleChange,
        onKeyDown: this.handleKeyDown,
      });

      var applyButton = React.createElement(ToolbarButton, {
        key: 'DYNAMIC_LINK_APPLY',
        name: 'APPLY',
        label: 'Apply',
        title: 'Apply dynamic link',
        tooltipDirection: 'up',
        onClick: () => this.apply(),
      });

      var removeButton = React.createElement(ToolbarButton, {
        key: 'DYNAMIC_LINK_REMOVE',
        name: 'REMOVE',
        label: 'Remove',
        title: 'Remove dynamic link',
        tooltipDirection: 'up',
        onClick: () => this.remove(),
      });

      var dropdown = React.createElement(
        'div',
        {
          'key': 'DYNAMIC_LINK_DROPDOWN',
          'className': 'Draftail--dtu-dropdown Draftail--dynamic-link-dropdown',
          'aria-expanded': this.state.isOpen,
        },
        input,
        React.createElement(
          'div',
          { className: 'Draftail--dynamic-link-actions' },
          applyButton,
          removeButton,
        ),
        this.renderContextGroups(),
      );

      var button = React.createElement(ToolbarButton, {
        name: control.type.toUpperCase(),
        active: !!active,
        title: active ? active : control.label,
        icon: icon,
        tooltipDirection: 'up',
        onClick: () => this.toggleDropdown(),
      });

      return React.createElement(
        'div',
        {
          id: 'Draftail--dynamic-link-control',
          className: 'Draftail--dtu-control',
          ref: this.controlRef,
        },
        dropdown,
        button,
      );
    }
  };

  window.draftail.registerPlugin(
    {
      type: control.type,
      inline: DynamicLinkControl,
    },
    'controls',
  );
})();
