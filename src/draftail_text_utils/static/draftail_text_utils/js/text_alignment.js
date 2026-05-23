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
  var ToolbarButton = window.Draftail.ToolbarButton;
  var data = window.draftailTextUtils || {};
  const type_ = 'text-alignment';
  const control = JSON.parse(
    document.getElementById(`draftail-plugin-control-${type_}`).textContent,
  );
  const options = control.data || [];

  // ── Helper to find active text alignment ──
  function getActiveOption(editorState) {
    const selection = editorState.getSelection();
    const block = editorState
      .getCurrentContent()
      .getBlockForKey(selection.getStartKey());
    const blockType = block.getType();
    return options.find((opt) => opt.type === blockType) || null;
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
      if (
        this.controlRef.current &&
        !this.controlRef.current.contains(event.target)
      ) {
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
      const newState = RichUtils.toggleBlockType(editorState, opt.type);
      onChange(newState);
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
          'className': 'Draftail--text-alignment-dropdown',
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
          className: 'Draftail--text-alignment-control',
          ref: this.controlRef,
        },
        dropdown,
        button,
      );
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
