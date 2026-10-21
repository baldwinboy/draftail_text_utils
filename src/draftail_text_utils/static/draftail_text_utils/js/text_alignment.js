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
  var DraftJS = window.DraftJS;
  var ToolbarButton = window.Draftail.ToolbarButton;
  var dt = window.DraftailTextUtils;
  var data = window.draftailTextUtils || {};
  const control = dt.parseControl('text-alignment');
  const options = control.data || [];

  // Legacy alignment was stored as a block type instead of block data.
  const LEGACY_ALIGNMENTS = {
    ALIGNMENT_LEFT: 'left',
    ALIGNMENT_CENTER: 'center',
    ALIGNMENT_RIGHT: 'right',
    ALIGNMENT_JUSTIFY: 'justify',
  };

  // ── Helper to find active text alignment ──
  function getActiveOption(editorState) {
    const selection = editorState.getSelection();
    const block = editorState
      .getCurrentContent()
      .getBlockForKey(selection.getStartKey());
    if (!block) return null;
    const alignment =
      block.getData().get('alignment') || LEGACY_ALIGNMENTS[block.getType()];
    return options.find((opt) => opt.value === alignment) || null;
  }

  function setAlignment(editorState, alignment) {
    const selection = editorState.getSelection();
    const startKey = selection.getStartKey();
    const endKey = selection.getEndKey();
    let content = editorState.getCurrentContent();
    let blockKey = startKey;

    while (blockKey) {
      let block = content.getBlockForKey(blockKey);
      const blockSelection = selection.merge({
        anchorKey: blockKey,
        anchorOffset: 0,
        focusKey: blockKey,
        focusOffset: block.getLength(),
        isBackward: false,
      });

      // Migrate legacy ALIGNMENT_* blocks to a regular paragraph plus block
      // data, so the new control can update them.
      if (LEGACY_ALIGNMENTS[block.getType()]) {
        content = DraftJS.Modifier.setBlockType(
          content,
          blockSelection,
          'unstyled',
        );
        block = content.getBlockForKey(blockKey);
      }

      let blockData = block.getData();
      if (alignment) {
        blockData = blockData.set('alignment', alignment);
      } else {
        blockData = blockData.delete('alignment');
      }

      content = DraftJS.Modifier.setBlockData(
        content,
        blockSelection,
        blockData,
      );

      if (blockKey === endKey) break;
      blockKey = content.getKeyAfter(blockKey);
    }

    return DraftJS.EditorState.forceSelection(
      DraftJS.EditorState.push(editorState, content, 'change-block-data'),
      selection,
    );
  }

  class TextAlignmentControl extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        isOpen: false,
      };
      this.controlRef = React.createRef();
    }

    componentDidMount() {
      document.addEventListener('mousedown', this.handleClickOutside);
    }

    componentWillUnmount() {
      document.removeEventListener('mousedown', this.handleClickOutside);
    }

    // ── close dropdown when clicking outside ──
    handleClickOutside = (event) => {
      if (dt.clickOutsideGuard(this.controlRef, event)) {
        this.setState({ isOpen: false });
      }
    };

    // ── toggle dropdown (used by button) ──
    toggleDropdown = (force) => {
      this.setState((prevState) => ({
        isOpen: typeof force === 'boolean' ? force : !prevState.isOpen,
      }));
    };

    // ── apply a text alignment ──
    handleOptionClick = (opt) => {
      const { getEditorState, onChange } = this.props;
      const editorState = getEditorState();
      const activeOption = getActiveOption(editorState);
      const removing = activeOption && activeOption.type === opt.type;

      onChange(setAlignment(editorState, removing ? null : opt.value));
      this.setState({ isOpen: false });
    };

    render() {
      const { getEditorState } = this.props;
      const editorState = getEditorState();
      const activeOption = getActiveOption(editorState);
      const isOpen = this.state.isOpen;
      const icon = `#icon-${activeOption ? activeOption.icon : control.icon}`;

      // ── Dropdown list ──
      const dropdown = React.createElement(
        'ul',
        {
          'id': 'Draftail--text-alignment-dropdown',
          'className': 'Draftail--dtu-dropdown Draftail--dtu-dropdown-row',
          'aria-expanded': isOpen,
        },
        options.map((opt) =>
          React.createElement(
            'li',
            {
              key: opt.type,
            },
            React.createElement(ToolbarButton, {
              name: opt.type.toUpperCase(),
              active: activeOption ? activeOption.type === opt.type : false,
              title: opt.label,
              className: 'Draftail--text-alignment-option',
              icon: `#icon-${opt.icon}`,
              tooltipDirection: 'up',
              onClick: () => this.handleOptionClick(opt),
            }),
          ),
        ),
      );

      // ── Toolbar button ──
      const button = React.createElement(ToolbarButton, {
        name: control.type.toUpperCase(),
        active: !!activeOption,
        title: control.label,
        icon: icon,
        tooltipDirection: 'up',
        onClick: () => this.toggleDropdown(),
      });

      return React.createElement(
        'div',
        {
          id: 'Draftail--text-alignment-control',
          className: 'Draftail--dtu-control',
          ref: this.controlRef,
        },
        dropdown,
        button,
      );
    }
  }

  function blockStyleFn(block) {
    const alignment = block.getData().get('alignment');
    if (!alignment) return null;
    return `Draftail-block--ALIGNMENT_${alignment.toUpperCase()}`;
  }

  // Add alignment classes to the editor blocks without changing their type.
  if (window.draftail && window.draftail.initEditor) {
    var originalInitEditor = window.draftail.initEditor;
    if (!originalInitEditor.__dtuTextAlignment) {
      var patchedInitEditor = function (selector, options, script) {
        options = options || {};
        options.plugins = (options.plugins || []).concat([
          {
            type: 'dtu-text-alignment',
            blockStyleFn: blockStyleFn,
          },
        ]);
        return Reflect.apply(originalInitEditor, window.draftail, [
          selector,
          options,
          script,
        ]);
      };
      patchedInitEditor.__dtuTextAlignment = true;
      window.draftail.initEditor = patchedInitEditor;
    }
  }

  window.draftail.registerPlugin(
    {
      type: control.type,
      inline: TextAlignmentControl,
    },
    'controls',
  );
})();
