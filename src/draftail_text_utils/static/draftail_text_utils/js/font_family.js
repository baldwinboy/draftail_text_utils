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
  var options = data.customFontFamilies || [];
  const type_ = 'font-family';
  const control = JSON.parse(
    document.getElementById(`draftail-plugin-control-${type_}`).textContent,
  );

  // ── Helper to find active font family ──
  function getActiveOption(editorState) {
    const currentStyle = editorState.getCurrentInlineStyle();
    return options.find((opt) => currentStyle.has(opt.type));
  }

  class FontFamilyControl extends React.Component {
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
      if (this.controlRef.current && !this.controlRef.current.contains(event.target)) {
        this.setState({ isOpen: false });
      }
    };

    // ── toggle dropdown (used by button) ──
    toggleDropdown = (force) => {
      this.setState((prevState) => ({
        isOpen: typeof force === 'boolean' ? force : !prevState.isOpen,
      }));
    };

    // ── apply a font family ──
    handleOptionClick = (opt) => {
      const { getEditorState, onChange } = this.props;
      let newState = getEditorState();
      const currentStyle = newState.getCurrentInlineStyle();

      // Remove any active font-family styles first
      options.forEach((item) => {
        if (currentStyle.has(item.type)) {
          newState = RichUtils.toggleInlineStyle(newState, item.type);
        }
      });

      // Apply the selected one
      newState = RichUtils.toggleInlineStyle(newState, opt.type);
      onChange(newState);

      // Close the dropdown
      this.setState({ isOpen: false });
    };

    render() {
      const { getEditorState } = this.props;
      const editorState = getEditorState();
      const activeOption = getActiveOption(editorState);
      const isOpen = this.state.isOpen;
      const icon = `#icon-${control.icon}`;

      // ── Dropdown list ──
      const dropdown = React.createElement(
        'ul',
        {
          className: 'Draftail--font-family-dropdown',
          'aria-expanded': isOpen,
        },
        options.map((opt) =>
          React.createElement(
            'li',
            {
              key: opt.type,
              onMouseDown: (e) => {
                // Prevent the blur on the button before the click is processed
                e.preventDefault();
                this.handleOptionClick(opt);
              },
              style: { fontFamily: opt.style.fontFamily },
              className: 'Draftail--font-family-option',
              'aria-selected': activeOption ? activeOption.type === opt.type : false,
            },
            opt.label,
          ),
        ),
      );

      // ── Toolbar button ──
      const button = React.createElement(ToolbarButton, {
        name: control.type.toUpperCase(),
        active: !!activeOption,
        title: activeOption ? activeOption.label : control.label,
        icon: icon,
        tooltipDirection: 'up',
        onClick: () => this.toggleDropdown(),
      });

      return React.createElement(
        'div',
        {
          className: 'Draftail--font-family-control',
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
      inline: FontFamilyControl,
    },
    'controls',
  );
})();