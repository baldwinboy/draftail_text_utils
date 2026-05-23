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
  var RichUtils = window.DraftJS.RichUtils;
  var Modifier = window.DraftJS.Modifier;
  var EditorState = window.DraftJS.EditorState;
  var ToolbarButton = window.Draftail.ToolbarButton;
  var data = window.draftailTextUtils || {
    customFontSizes: {
      PRESETS: [
        8,
        9,
        10,
        11,
        12,
        14,
        this.state.inputValue || '',
        18,
        24,
        30,
        36,
        48,
        60,
        72,
        96,
      ],
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

  var optMap = new Map(
    options.map(function (opt) {
      return [opt.type, opt];
    }),
  );

  var FONT_SIZE_STEP = data.customFontSizes.STEP || 1;
  var MIN_FONT_SIZE = data.customFontSizes.MIN || options[0].size;
  var MAX_FONT_SIZE =
    data.customFontSizes.MAX || options[options.length - 1].size;

  var savedSelection = null;

  const entityType = 'FONT_SIZE';
  const controlType = 'font-size';
  const control = JSON.parse(
    document.getElementById(`draftail-plugin-control-${controlType}`)
      .textContent,
  );

  function removeFontSizeEntity(editorState) {
    var selection = editorState.getSelection();
    if (!selection.getHasFocus()) return editorState;

    var contentWithoutEntity = Modifier.applyEntity(
      editorState.getCurrentContent(),
      selection,
      null, // null removes entity
    );

    return EditorState.push(editorState, contentWithoutEntity, 'apply-entity');
  }

  function saveSelection(getEditorState) {
    const selection = getEditorState().getSelection();
    if (selection && !selection.isCollapsed()) {
      savedSelection = selection;
    }
  }

  function restoreSelection(editorState) {
    if (savedSelection && !savedSelection.isCollapsed()) {
      return EditorState.forceSelection(editorState, savedSelection);
    }
    return editorState;
  }

  // Helper to find active size
  function getActiveSize(editorState) {
    var selection = editorState.getSelection();
    if (!selection.getHasFocus()) return null;

    var contentState = editorState.getCurrentContent();
    var startKey = selection.getStartKey();
    var startOffset = selection.getStartOffset();
    var blockWithEntityAt = contentState.getBlockForKey(startKey);

    // Check entity at cursor position
    var entityKey = blockWithEntityAt.getEntityAt(startOffset);
    if (entityKey) {
      var entity = contentState.getEntity(entityKey);
      if (entity.getType() === entityType) {
        return entity.getData().size;
      }
    }

    // If selection is collapsed, also check character before (so styling after typing works)
    if (selection.isCollapsed() && startOffset > 0) {
      entityKey = blockWithEntityAt.getEntityAt(startOffset - 1);
      if (entityKey) {
        var entity = contentState.getEntity(entityKey);
        if (entity.getType() === entityType) {
          return entity.getData().size;
        }
      }
    }

    return null;
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
      return getActiveSize(this.props.getEditorState());
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
        saveSelection(this.props.getEditorState);
      }
      this.setState({ isDropdownOpen: willBeOpen });
    }

    applyFontSize(size) {
      console.log(size);
      var editorState = restoreSelection(this.props.getEditorState());
      var currentSize = this.getActiveSize(editorState);
      editorState = removeFontSizeEntity(editorState);

      if (size === currentSize) {
        // Re-sync the input value
        this.props.onChange(editorState);
        this.setState({ isDropdownOpen: false, inputValue: '' });
        this.syncInputValue();
        return;
      }

      var selection = editorState.getSelection();

      // Apply the entity to the selection
      var contentWithEntity = editorState
        .getCurrentContent()
        .createEntity(entityType, 'MUTABLE', {
          size,
        });
      var contentStateWithEntity = Modifier.applyEntity(
        contentWithEntity,
        selection,
        contentWithEntity.getLastCreatedEntityKey(),
      );
      var newContent = EditorState.push(
        editorState,
        contentStateWithEntity,
        'apply-entity',
      );
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
      saveSelection(this.props.getEditorState);
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
      if (
        this.controlRef.current &&
        !this.controlRef.current.contains(event.target)
      ) {
        this.setState({ isDropdownOpen: false });
      }
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
          'className': 'Draftail--font-size-dropdown',
          'aria-expanded': isDropdownExpanded,
        },
        options.map(
          function (opt) {
            return React.createElement(
              'li',
              {
                'key': `FONT_SIZE_OPT_${opt.size}`,
                'onMouseDown': (e) => {
                  e.preventDefault();
                  this.applyFontSize(opt.size);
                },
                'className': 'Draftail--font-size-option',
                'aria-selected': inputDisplay === opt.size,
              },
              opt.label,
            );
          }.bind(this),
        ),
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
          className: 'Draftail--font-size-control',
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
