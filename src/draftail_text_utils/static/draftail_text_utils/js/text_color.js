(function () {
  var React = window.React;
  var ToolbarButton = window.Draftail.ToolbarButton;
  var dt = window.DraftailTextUtils;
  var data = window.draftailTextUtils || {};

  var options = data.customTextColors || [];

  const entityType = 'TEXT_STYLE';
  const control = dt.parseControl('text-color');

  var TextColorControl = class TextColorControl extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        isDropdownOpen: false,
      };
      this.controlRef = React.createRef();
    }

    componentDidMount() {
      document.addEventListener('mousedown', this.handleClickOutside);
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);
    }

    getActiveColor() {
      return dt.getActiveEntityData(
        this.props.getEditorState(),
        entityType,
        'color',
      );
    }

    toggleDropdown(force) {
      const willBeOpen =
        typeof force === 'boolean' ? force : !this.state.isDropdownOpen;
      if (willBeOpen && !this.state.isDropdownOpen) {
        dt.saveSelection(this.props.getEditorState);
      }
      this.setState({ isDropdownOpen: willBeOpen });
    }

    applyTextColor(newColor) {
      var color = newColor === 'transparent' ? '#00000000' : newColor;
      var editorState = dt.restoreSelection(this.props.getEditorState());
      var currentColor = this.getActiveColor(editorState);

      if (color === currentColor) {
        editorState = dt.removeStyleProperty(editorState, entityType, 'color');
        this.props.onChange(editorState);
        this.setState({ isDropdownOpen: false });
        return;
      }

      var newContent = dt.mergeStyleEntity(editorState, entityType, { color });
      this.props.onChange(newContent);
      this.setState({ isDropdownOpen: false });
    }

    handleNativeColorChange = (e) => {
      this.applyTextColor(e.target.value);
    };

    handleClickOutside = (event) => {
      if (dt.clickOutsideGuard(this.controlRef, event)) {
        this.setState({ isDropdownOpen: false });
      }
    };

    createOptElement = (opt) => {
      return React.createElement(
        'li',
        {
          key: `TEXT_COLOR_OPT_${opt.key.toUpperCase()}`,
          className: 'Draftail--dtu-color-option-wrapper',
        },
        React.createElement(ToolbarButton, {
          name: opt.value === 'transparent' ? '#00000000' : opt.value,
          active: this.getActiveColor() === opt.value,
          title: opt.label,
          label: '\u2713',
          tooltipDirection: 'up',
          className: 'Draftail--dtu-color-option',
          onClick: () => this.applyTextColor(opt.value),
        }),
      );
    };

    render() {
      const icon = `#icon-${control.icon}`;

      var activeColor = this.getActiveColor();
      var isDropdownExpanded = this.state.isDropdownOpen;

      var input = React.createElement(
        'li',
        {
          'key': 'TEXT_COLOR_CTRL_INPUT_WRAPPER',
          'id': 'Draftail--text-color-input-wrapper',
          'className': 'Draftail--dtu-color-input-wrapper',
          'data-draftail-balloon': 'down',
          'aria-label': 'Select custom color',
        },
        React.createElement('input', {
          key: 'TEXT_COLOR_CTRL_INPUT',
          type: 'color',
          defaultValue: activeColor || '#000000',
          onChange: this.handleNativeColorChange,
        }),
      );

      var hr = React.createElement('hr', {
        key: 'TEXT_COLOR_CTRL_HR',
        className: 'Draftail--dtu-color-hr',
      });

      var dropdown = React.createElement(
        'ul',
        {
          'id': 'Draftail--text-color-dropdown',
          'className': 'Draftail--dtu-dropdown Draftail--dtu-dropdown-palette',
          'aria-expanded': isDropdownExpanded,
        },
        options.map(this.createOptElement),
        hr,
        input,
      );

      var button = React.createElement(ToolbarButton, {
        name: control.type.toUpperCase(),
        active: !!activeColor,
        title: control.label,
        icon: icon,
        tooltipDirection: 'up',
        onClick: () => this.toggleDropdown(),
      });

      return React.createElement(
        'div',
        {
          key: 'TEXT_COLOR_CTRL',
          id: 'Draftail--text-color-control',
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
      inline: TextColorControl,
    },
    'controls',
  );
})();
