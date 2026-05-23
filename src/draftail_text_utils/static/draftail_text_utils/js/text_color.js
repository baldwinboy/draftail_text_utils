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

// CSS Color Component
// https://github.com/argyleink/css-color-component

(function () {
  var React = window.React;
  var RichUtils = window.DraftJS.RichUtils;
  var Modifier = window.DraftJS.Modifier;
  var EditorState = window.DraftJS.EditorState;
  var ToolbarButton = window.Draftail.ToolbarButton;
  var data = window.draftailTextUtils || {};

  // Build options from config
  var options = data.customTextColors || [];
  var optMap = data.customTextColorStyleMap || {};

  var savedSelection = null;

  const entityType = 'TEXT_COLOR';
  const controlType = 'text-color';
  const control = JSON.parse(
    document.getElementById(`draftail-plugin-control-${controlType}`)
      .textContent,
  );

  function removeTextColorEntity(editorState) {
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

  // Helper to find active color
  function getActiveColor(editorState) {
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
        return entity.getData().color;
      }
    }

    // If selection is collapsed, also check character before (so styling after typing works)
    if (selection.isCollapsed() && startOffset > 0) {
      entityKey = blockWithEntityAt.getEntityAt(startOffset - 1);
      if (entityKey) {
        var entity = contentState.getEntity(entityKey);
        if (entity.getType() === entityType) {
          return entity.getData().color;
        }
      }
    }

    return null;
  }

  // The control component
  var TextColorControl = class TextColorControl extends React.Component {
    constructor(props) {
      super(props); // getEditorState, onChange
      this.state = {
        isDropdownOpen: false,
        inputValue: '#000000',
        isInputFocused: false,
      };
      this.controlRef = React.createRef();
    }

    // lifecycle
    componentDidMount() {
      this.syncInputValue();
      document.addEventListener('mousedown', this.handleClickOutside);

      // Listen to CSS Color Component events
      var inputEl = document.querySelector('#Draftail--text-color-input');
      if (inputEl) {
        inputEl.addEventListener('open', this.handleInputFocus);
        inputEl.addEventListener('close', this.handleInputBlur);
        inputEl.addEventListener('change', this.handleInputChange);
      }
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);

      // Unsubscribe from CSS Color Component events
      var inputEl = document.querySelector('#Draftail--text-color-input');
      if (inputEl) {
        inputEl.removeEventListener('open', this.handleInputFocus);
        inputEl.removeEventListener('close', this.handleInputBlur);
        inputEl.removeEventListener('change', this.handleInputChange);
      }
    }

    componentDidUpdate() {
      this.syncInputValue(); // always runs, but guarded internally
    }

    // helpers
    getActiveColor() {
      return getActiveColor(this.props.getEditorState());
    }

    syncInputValue() {
      // While the user is editing, never overwrite their input
      if (this.state.isInputFocused || this.state.isDropdownOpen) {
        return;
      }

      var activeColor = this.getActiveColor();
      var newValue = activeColor || '';

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

    applyTextColor(newColor) {
      var color = newColor === 'transparent' ? '#00000000' : newColor;
      var editorState = restoreSelection(this.props.getEditorState());
      var currentColor = this.getActiveColor(editorState);
      editorState = removeTextColorEntity(editorState);

      if (color === currentColor) {
        // Re-sync the input value
        this.props.onChange(editorState);
        this.setState({ isDropdownOpen: false, inputValue: '#000000' });
        this.syncInputValue();
        return;
      }

      var selection = editorState.getSelection();

      // Apply the entity to the selection
      var contentWithEntity = editorState
        .getCurrentContent()
        .createEntity(entityType, 'MUTABLE', {
          color,
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
      this.setState({ isDropdownOpen: false, inputValue: String(color) });
      this.syncInputValue();
    }

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
      this.applyTextColor(e.detail.value);
    };

    handleInputKeyDown = (e) => {
      if (e.key === 'Escape') {
        this.toggleDropdown(false);
        this.syncInputValue();
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        this.applyTextColor(this.state.inputValue);
        return;
      }
    };

    handleClickOutside = (event) => {
      if (
        this.controlRef.current &&
        !this.controlRef.current.contains(event.target)
      ) {
        this.setState({ isDropdownOpen: false, isInputFocused: false });
        var inputEl = document.querySelector('#Draftail--text-color-input');
        if (inputEl) {
          inputEl.close();
        }
      }
    };

    createOptElement = (opt) => {
      return React.createElement(
        'li',
        {
          key: `TEXT_COLOR_OPT_${opt.key.toUpperCase()}`,
          className: 'Draftail--text-color-option-wrapper',
        },
        React.createElement(ToolbarButton, {
          name: opt.value === 'transparent' ? '#00000000' : opt.value,
          active: this.getActiveColor() === opt.value,
          title: opt.label,
          label: '\u2713',
          tooltipDirection: 'up',
          className: 'Draftail--text-color-option',
          onClick: () => this.applyTextColor(opt.value),
        }),
      );
    };

    // render
    render() {
      const icon = `#icon-${control.icon}`;

      var activeColor = this.getActiveColor();
      var inputDisplay = this.state.inputValue;
      var isDropdownExpanded = this.state.isDropdownOpen;

      var input = React.createElement(
        'li',
        {
          'key': 'TEXT_COLOR_CTRL_INPUT_WRAPPER',
          'className': 'Draftail--text-color-input-wrapper',
          'data-draftail-balloon': 'down',
          'aria-label': 'Select custom color',
        },
        React.createElement('color-input', {
          key: 'TEXT_COLOR_CTRL_INPUT',
          id: 'Draftail--text-color-input',
          className: 'Draftail--text-color-input',
          defaultValue: activeColor || '',
          value: inputDisplay,
          onKeyDown: this.handleInputKeyDown,
        }),
      );

      var hr = React.createElement('hr', {
        key: 'TEXT_COLOR_CTRL_HR',
        className: 'Draftail--text-color-hr',
      });

      var dropdown = React.createElement(
        'ul',
        {
          'id': 'Draftail--text-color-dropdown',
          'className': 'Draftail--text-color-dropdown',
          'aria-expanded': isDropdownExpanded,
        },
        options.map(this.createOptElement),
        hr,
        input,
      );

      // ── Toolbar button ──
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
          className: 'Draftail--text-color-control',
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
