// https://github.com/wagtail/draftail/blob/main/src/components/Toolbar/ToolbarButton.tsx
// export interface ToolbarButtonProps {
//   name?: string;
//   active?: boolean;
//   label?: string | null;
//   title?: string | null;
//   icon?: IconProp | null;
//   className?: string | null;
//   tooltipDirection?: "up" | "down";
//   onClick?: ((name: string) => void) | null;
// }

(function () {
  var React = window.React;
  var ToolbarButton = window.Draftail.ToolbarButton;
  var dt = window.DraftailTextUtils;
  var data = window.draftailTextUtils || {
    customFontSizes: {
      PRESETS: [8, 9, 10, 11, 12, 14, 16, 18, 24, 30, 36, 48, 60, 72, 96],
    },
  };

  // Build options from config
  var options = data.customFontSizes.PRESETS.map(function (size) {
    return {
      label: String(size),
      type: 'FONT_SIZE_' + size,
      style: { fontSize: size + 'px' },
      size: size,
    };
  });

  var FONT_SIZE_STEP = data.customFontSizes.STEP || 1;
  var MIN_FONT_SIZE = data.customFontSizes.MIN || options[0].size;
  var MAX_FONT_SIZE =
    data.customFontSizes.MAX || options[options.length - 1].size;

  const entityType = 'TEXT_STYLE';
  const control = dt.parseControl('font-size');

  // The control component
  var FontSizeControl = class FontSizeControl extends React.Component {
    constructor(props) {
      super(props); // getEditorState, onChange
      this.state = {
        isDropdownOpen: false,
        inputValue: '',
        isInputFocused: false,
      };
      this.controlRef = React.createRef();
    }

    // lifecycle
    componentDidMount() {
      this.syncInputValue();
      document.addEventListener('mousedown', this.handleClickOutside);
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);
    }

    componentDidUpdate() {
      this.syncInputValue(); // always runs, but guarded internally
    }

    // helpers
    getActiveSize() {
      return dt.getActiveEntityData(
        this.props.getEditorState(),
        entityType,
        'size',
      );
    }

    syncInputValue() {
      // While the user is editing, never overwrite their input
      if (this.state.isInputFocused || this.state.isDropdownOpen) {
        return;
      }

      var activeSize = this.getActiveSize();
      var newValue = activeSize || '';

      if (this.state.inputValue !== newValue) {
        this.setState({ inputValue: newValue });
      }
    }

    toggleDropdown(force) {
      const willBeOpen =
        typeof force === 'boolean' ? force : !this.state.isDropdownOpen;
      if (willBeOpen && !this.state.isDropdownOpen) {
        dt.saveSelection(this.props.getEditorState);
      }
      this.setState({ isDropdownOpen: willBeOpen });
    }

    applyFontSize(size) {
      var editorState = dt.restoreSelection(this.props.getEditorState());
      var currentSize = this.getActiveSize(editorState);

      if (size === currentSize) {
        editorState = dt.removeStyleProperty(editorState, entityType, 'size');
        this.props.onChange(editorState);
        this.setState({ isDropdownOpen: false, inputValue: '' });
        this.syncInputValue();
        return;
      }

      var newContent = dt.mergeStyleEntity(editorState, entityType, { size });
      this.props.onChange(newContent);

      // Re-sync the input value
      this.setState({ isDropdownOpen: false, inputValue: String(size) });
      this.syncInputValue();
    }

    increment() {
      var activeSize = this.getActiveSize();
      var currentSize = isNaN(activeSize || this.state.inputValue || 'NaN')
        ? 16
        : parseInt(activeSize || this.state.inputValue);
      this.applyFontSize(Math.min(MAX_FONT_SIZE, currentSize + 1));
    }

    decrement() {
      var activeSize = this.getActiveSize();
      var currentSize = isNaN(activeSize || this.state.inputValue || 'NaN')
        ? 16
        : parseInt(activeSize || this.state.inputValue);
      this.applyFontSize(Math.max(MIN_FONT_SIZE, currentSize - 1));
    }

    // event handlers
    handleInputMouseDown = (e) => {
      this.toggleDropdown();
    };

    handleInputFocus = () => {
      dt.saveSelection(this.props.getEditorState);
      this.setState({ isInputFocused: true });
      if (!this.state.isDropdownOpen) {
        this.setState({ isDropdownOpen: true });
      }
    };

    handleInputBlur = () => {
      // When leaving the field, clear the focus flag and re‑sync (will clear if no style)
      this.setState({ isInputFocused: false }, () => {
        this.syncInputValue();
      });
    };

    handleInputChange = (e) => {
      this.setState({ inputValue: e.target.value.replace(/[^0-9]/g, '') });
    };

    handleInputKeyDown = (e) => {
      if (e.key === 'Escape') {
        this.toggleDropdown(false);
        this.syncInputValue();
        return;
      }

      if (['ArrowUp', 'ArrowDown', 'Enter'].includes(e.key)) {
        e.preventDefault();
        if (e.key === 'Enter') {
          var size = parseInt(this.state.inputValue, 10);
          if (size > 0 && size <= 400) {
            this.applyFontSize(size);
          } else {
            this.syncInputValue();
          }
          return;
        }

        if (e.key === 'ArrowUp') {
          this.increment();
          return;
        }

        this.decrement();
        return;
      }
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
          'key': `FONT_SIZE_OPT_${opt.size}`,
          'onMouseDown': (e) => {
            e.preventDefault();
            this.applyFontSize(opt.size);
          },
          'className': 'Draftail--dtu-option Draftail--font-size-option',
          'aria-selected': this.state.inputValue === opt.size,
        },
        opt.label,
      );
    };

    // render
    render() {
      var activeSize = this.getActiveSize();
      var inputDisplay = this.state.inputValue;
      var isDropdownExpanded = this.state.isDropdownOpen;
      var dropdown = React.createElement(
        'ul',
        {
          'id': 'Draftail--font-size-dropdown',
          'className': 'Draftail--dtu-dropdown',
          'aria-expanded': isDropdownExpanded,
        },
        options.map(this.createOptElement),
      );

      var decrementBtn = React.createElement(ToolbarButton, {
        key: `FONT_SIZE_CTRL_DECREMENT`,
        name: 'DECREMENT',
        title: 'Decrease font size',
        label: '-',
        tooltipDirection: 'up',
        className: 'Draftail--font-size-decrement',
        onClick: this.decrement.bind(this),
      });

      var incrementBtn = React.createElement(ToolbarButton, {
        key: `FONT_SIZE_CTRL_INCREMENT`,
        name: 'INCREMENT',
        title: 'Increase font size',
        label: '+',
        tooltipDirection: 'up',
        className: 'Draftail--font-size-increment',
        onClick: this.increment.bind(this),
      });

      var input = React.createElement(
        'div',
        {
          'key': 'FONT_SIZE_CTRL_INPUT_WRAPPER',
          'className': 'Draftail--font-size-input-wrapper',
          'data-draftail-balloon': 'up',
          'aria-label': control.label,
          'aria-controls': 'Draftail--font-size-dropdown',
        },
        React.createElement('input', {
          key: 'FONT_SIZE_CTRL_INPUT',
          id: 'Draftail--font-size-input',
          className: 'Draftail--font-size-input',
          type: 'text',
          defaultValue: activeSize || '',
          value: inputDisplay,
          placeholder: 'Font Size',
          onMouseDown: this.handleInputMouseDown,
          onFocus: this.handleInputFocus,
          onBlur: this.handleInputBlur,
          onChange: this.handleInputChange,
          onKeyDown: this.handleInputKeyDown,
        }),
      );

      var controlRow = React.createElement(
        'div',
        {
          key: 'FONT_SIZE_CTRL_ROW',
          className: 'Draftail--font-size-control-row',
        },
        decrementBtn,
        input,
        incrementBtn,
      );

      return React.createElement(
        'div',
        {
          key: 'FONT_SIZE_CTRL',
          id: 'Draftail--font-size-control',
          className: 'Draftail--dtu-control',
          ref: this.controlRef,
        },
        controlRow,
        dropdown,
      );
    }
  };
  window.draftail.registerPlugin(
    {
      type: control.type,
      inline: FontSizeControl,
    },
    'controls',
  );
})();
