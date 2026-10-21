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

  function normaliseSize(value) {
    if (value === null || value === undefined || value === '') return '';
    var parsed = parseInt(value, 10);
    return isNaN(parsed) ? String(value) : String(parsed);
  }

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
      this.replaceOnNextDigit = false;
    }

    // lifecycle
    componentDidMount() {
      this.syncInputValue();
      document.addEventListener('mousedown', this.handleClickOutside);
      document.addEventListener('keydown', this.handleDocumentKeyDown, true);
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);
      document.removeEventListener('keydown', this.handleDocumentKeyDown, true);
    }

    componentDidUpdate() {
      this.syncInputValue(); // always runs, but guarded internally
    }

    // helpers
    getActiveSize(editorState) {
      return dt.getActiveEntityData(
        editorState || this.props.getEditorState(),
        entityType,
        'size',
      );
    }

    syncInputValue() {
      // While the user is editing, never overwrite their input
      if (this.state.isInputFocused || this.state.isDropdownOpen) {
        return;
      }

      var newValue = normaliseSize(this.getActiveSize());

      if (this.state.inputValue !== newValue) {
        this.setState({ inputValue: newValue });
      }
    }

    stopEditing() {
      this.replaceOnNextDigit = false;
      this.setState({ isDropdownOpen: false, isInputFocused: false }, () => {
        this.syncInputValue();
      });
    }

    applyFontSize(size) {
      var editorState = dt.restoreSelection(this.props.getEditorState());
      var currentSize = normaliseSize(this.getActiveSize(editorState));

      if (String(size) === currentSize) {
        editorState = dt.removeStyleProperty(editorState, entityType, 'size');
        this.props.onChange(editorState);
        this.replaceOnNextDigit = false;
        this.setState({
          isDropdownOpen: false,
          isInputFocused: false,
          inputValue: '',
        });
        this.syncInputValue();
        return;
      }

      var newContent = dt.mergeStyleEntity(editorState, entityType, { size });
      this.props.onChange(newContent);

      // Re-sync the input value
      this.replaceOnNextDigit = false;
      this.setState({
        isDropdownOpen: false,
        isInputFocused: false,
        inputValue: String(size),
      });
      this.syncInputValue();
    }

    increment() {
      var value =
        this.state.isInputFocused && this.state.inputValue
          ? this.state.inputValue
          : this.getActiveSize();
      var currentSize = isNaN(value || 'NaN') ? 16 : parseInt(value);
      this.applyFontSize(Math.min(MAX_FONT_SIZE, currentSize + FONT_SIZE_STEP));
    }

    decrement() {
      var value =
        this.state.isInputFocused && this.state.inputValue
          ? this.state.inputValue
          : this.getActiveSize();
      var currentSize = isNaN(value || 'NaN') ? 16 : parseInt(value);
      this.applyFontSize(Math.max(MIN_FONT_SIZE, currentSize - FONT_SIZE_STEP));
    }

    // event handlers
    handleInputMouseDown = (e) => {
      // Do not focus the input: that would blur the editor, clear Draftail's
      // selection focus, and unmount the floating toolbar. Keep the editor
      // focused and route keyboard input to the control instead.
      e.preventDefault();
      dt.saveSelection(this.props.getEditorState);
      this.replaceOnNextDigit = true;
      this.setState({ isDropdownOpen: true, isInputFocused: true });
    };

    handleDocumentKeyDown = (e) => {
      if (!this.state.isInputFocused) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      if (/^[0-9]$/.test(e.key)) {
        e.preventDefault();
        e.stopPropagation();
        var nextValue = this.replaceOnNextDigit
          ? e.key
          : (this.state.inputValue || '') + e.key;
        this.replaceOnNextDigit = false;
        this.setState({ inputValue: nextValue });
        return;
      }

      if (e.key === 'Backspace') {
        e.preventDefault();
        e.stopPropagation();
        this.replaceOnNextDigit = false;
        this.setState({
          inputValue: (this.state.inputValue || '').slice(0, -1),
        });
        return;
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        e.stopPropagation();
        this.increment();
        return;
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        e.stopPropagation();
        this.decrement();
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
        var size = parseInt(this.state.inputValue, 10);
        if (size >= MIN_FONT_SIZE && size <= MAX_FONT_SIZE) {
          this.applyFontSize(size);
        } else {
          this.stopEditing();
        }
        return;
      }

      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        this.stopEditing();
        return;
      }

      if (e.key === 'Tab') {
        this.stopEditing();
        return;
      }

      // Keep all other typing/navigation out of the editor while the control
      // is capturing input.
      if (
        e.key.length === 1 ||
        [
          'Delete',
          'Home',
          'End',
          'PageUp',
          'PageDown',
          'ArrowLeft',
          'ArrowRight',
        ].includes(e.key)
      ) {
        e.preventDefault();
        e.stopPropagation();
      }
    };

    handleClickOutside = (event) => {
      if (dt.clickOutsideGuard(this.controlRef, event)) {
        this.replaceOnNextDigit = false;
        this.setState({ isDropdownOpen: false, isInputFocused: false }, () => {
          this.syncInputValue();
        });
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
          'aria-selected':
            normaliseSize(this.state.inputValue) === String(opt.size),
        },
        opt.label,
      );
    };

    // render
    render() {
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
          value: inputDisplay,
          placeholder: 'Font Size',
          tabIndex: -1,
          onMouseDown: this.handleInputMouseDown,
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
