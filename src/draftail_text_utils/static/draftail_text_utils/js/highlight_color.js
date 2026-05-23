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
  var options = data.customHighlightColors || [];
  var optMap = data.customHighlightColorStyleMap || {};

  var savedSelection = null;

  const entityType = 'HIGHLIGHT_COLOR';
  const controlType = 'highlight-color';
  const control = JSON.parse(
    document.getElementById(`draftail-plugin-control-${controlType}`)
      .textContent,
  );

  function removeHighlightColorEntity(editorState) {
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
  function getActiveHighlightColor(editorState) {
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
        return entity.getData().backgroundColor;
      }
    }

    // If selection is collapsed, also check character before (so styling after typing works)
    if (selection.isCollapsed() && startOffset > 0) {
      entityKey = blockWithEntityAt.getEntityAt(startOffset - 1);
      if (entityKey) {
        var entity = contentState.getEntity(entityKey);
        if (entity.getType() === entityType) {
          return entity.getData().backgroundColor;
        }
      }
    }

    return null;
  }

  // The control component
  var HighlightColorControl = class HighlightColorControl
    extends React.Component
  {
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

      // Listen to CSS Color Component events
      var inputEl = document.querySelector('#Draftail--highlight-color-input');
      if (inputEl) {
        inputEl.addEventListener('open', this.handleInputFocus);
        inputEl.addEventListener('close', this.handleInputBlur);
        inputEl.addEventListener('change', this.handleInputChange);
      }
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);

      // Unsubscribe from CSS Color Component events
      var inputEl = document.querySelector('#Draftail--highlight-color-input');
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
    getActiveHighlightColor() {
      return getActiveHighlightColor(this.props.getEditorState());
    }

    syncInputValue() {
      // While the user is editing, never overwrite their input
      if (this.state.isInputFocused || this.state.isDropdownOpen) {
        return;
      }

      var activeHighlightColor = this.getActiveHighlightColor();
      var newValue = activeHighlightColor || '';

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

    applyHighlightColor(newColor) {
      var backgroundColor = newColor === 'transparent' ? '#00000000' : newColor;
      var editorState = restoreSelection(this.props.getEditorState());
      var currentColor = this.getActiveHighlightColor(editorState);
      editorState = removeHighlightColorEntity(editorState);

      if (backgroundColor === currentColor) {
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
          backgroundColor,
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
      this.setState({
        isDropdownOpen: false,
        inputValue: String(backgroundColor),
      });
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
      this.applyHighlightColor(e.detail.value);
    };

    handleInputKeyDown = (e) => {
      if (e.key === 'Escape') {
        this.toggleDropdown(false);
        this.syncInputValue();
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        this.applyHighlightColor(this.state.inputValue);
        return;
      }
    };

    handleClickOutside = (event) => {
      if (
        this.controlRef.current &&
        !this.controlRef.current.contains(event.target)
      ) {
        this.setState({ isDropdownOpen: false, isInputFocused: false });
        var inputEl = document.querySelector(
          '#Draftail--highlight-color-input',
        );
        if (inputEl) {
          inputEl.close();
        }
      }
    };

    createOptElement = (opt) => {
      return React.createElement(
        'li',
        {
          key: `HIGHLIGHT_COLOR_OPT_${opt.key.toUpperCase()}`,
          className: 'Draftail--highlight-color-option-wrapper',
        },
        React.createElement(ToolbarButton, {
          name: opt.value === 'transparent' ? '#00000000' : opt.value,
          active: this.getActiveHighlightColor() === opt.value,
          title: opt.label,
          label: '\u2713',
          tooltipDirection: 'up',
          className: 'Draftail--highlight-color-option',
          onClick: () => this.applyHighlightColor(opt.value),
        }),
      );
    };

    // render
    render() {
      const icon = `#icon-${control.icon}`;

      var activeHighlightColor = this.getActiveHighlightColor();
      var inputDisplay = this.state.inputValue;
      var isDropdownExpanded = this.state.isDropdownOpen;

      var input = React.createElement(
        'li',
        {
          'key': 'HIGHLIGHT_COLOR_CTRL_INPUT_WRAPPER',
          'className': 'Draftail--highlight-color-input-wrapper',
          'data-draftail-balloon': 'down',
          'aria-label': 'Select custom highlight color',
        },
        React.createElement('color-input', {
          key: 'HIGHLIGHT_COLOR_CTRL_INPUT',
          id: 'Draftail--highlight-color-input',
          className: 'Draftail--highlight-color-input',
          defaultValue: activeHighlightColor || '#000000',
          value: inputDisplay || '#000000',
          onKeyDown: this.handleInputKeyDown,
        }),
      );

      var hr = React.createElement('hr', {
        key: 'HIGHLIGHT_COLOR_CTRL_HR',
        className: 'Draftail--highlight-color-hr',
      });

      var dropdown = React.createElement(
        'ul',
        {
          'id': 'Draftail--highlight-color-dropdown',
          'className': 'Draftail--highlight-color-dropdown',
          'aria-expanded': isDropdownExpanded,
        },
        options.map(this.createOptElement),
        hr,
        input,
      );

      // ── Toolbar button ──
      var button = React.createElement(ToolbarButton, {
        name: control.type.toUpperCase(),
        active: !!activeHighlightColor,
        title: control.label,
        icon: icon,
        tooltipDirection: 'up',
        onClick: () => this.toggleDropdown(),
      });

      return React.createElement(
        'div',
        {
          key: 'HIGHLIGHT_COLOR_CTRL',
          className: 'Draftail--highlight-color-control',
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
      inline: HighlightColorControl,
    },
    'controls',
  );
})();
