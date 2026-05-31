(function () {
  if (!window.draftail) return;

  var React = window.React;
  var Component = window.React.Component;
  var ENTITY_TYPE = 'TEXT_STYLE';

  var StyledLinkSource = function (_props) {
    Component.call(this, _props);
    this.onChosen = this.onChosen.bind(this);
    this.onClose = this.onClose.bind(this);
  };

  StyledLinkSource.prototype = Object.create(Component.prototype);
  StyledLinkSource.prototype.constructor = StyledLinkSource;

  StyledLinkSource.prototype.render = function () {
    return null;
  };

  StyledLinkSource.prototype.componentDidMount = function () {
    var _this2 = this;
    var props = this.props;
    var onClose = props.onClose;
    var entity = props.entity;
    var editorState = props.editorState;

    var linkText = '';
    if (editorState) {
      var selection = editorState.getSelection();
      if (selection && !selection.isCollapsed()) {
        linkText = editorState
          .getCurrentContent()
          .getPlainText()
          .substring(selection.getStartOffset(), selection.getEndOffset());
      }
    }

    var chooserUrls = (props.entityType && props.entityType.chooserUrls) || {};

    var data = null;
    if (entity) {
      data = entity.getData();
    }

    var url = chooserUrls.pageChooser;
    var urlParams = {
      page_type: 'wagtailcore.page',
      allow_external_link: true,
      allow_email_link: true,
      allow_phone_link: true,
      allow_anchor_link: true,
      link_text: linkText,
    };

    if (data) {
      if (data.id) {
        url = data.parentId
          ? chooserUrls.pageChooser + data.parentId + '/'
          : chooserUrls.pageChooser;
      } else if (data.url && data.url.startsWith('mailto:')) {
        url = chooserUrls.emailLinkChooser;
        urlParams.link_url = data.url.replace('mailto:', '');
      } else if (data.url && data.url.startsWith('tel:')) {
        url = chooserUrls.phoneLinkChooser;
        urlParams.link_url = data.url.replace('tel:', '');
      } else if (data.url && data.url.startsWith('#')) {
        url = chooserUrls.anchorLinkChooser;
        urlParams.link_url = data.url.replace('#', '');
      } else if (data.url) {
        url = chooserUrls.externalLinkChooser;
        urlParams.link_url = data.url;
      }
    }

    $(document.body).on('hidden.bs.modal', this.onClose);
    this.workflow = window.ModalWorkflow({
      url: url,
      urlParams: urlParams,
      onload: window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      responses: {
        pageChosen: this.onChosen,
      },
      onError: function () {
        window.alert('Server Error');
        onClose();
      },
    });
  };

  StyledLinkSource.prototype.componentWillUnmount = function () {
    this.workflow = null;
    $(document.body).off('hidden.bs.modal', this.onClose);
  };

  StyledLinkSource.prototype.filterEntityData = function (chosenData) {
    return chosenData.id
      ? {
          url: chosenData.url,
          id: chosenData.id,
          parentId: chosenData.parentId,
        }
      : { url: chosenData.url };
  };

  StyledLinkSource.prototype.onChosen = function (chosenData) {
    var Modifier = window.DraftJS.Modifier;
    var EditorState = window.DraftJS.EditorState;
    var props = this.props;
    var editorState = props.editorState;
    var entity = props.entity;
    var onComplete = props.onComplete;

    var contentState = editorState.getCurrentContent();
    var selection = editorState.getSelection();
    var entityData = this.filterEntityData(chosenData);

    var newContent = contentState;
    var newEntityKey = null;

    if (entity) {
      var existingData = entity.getData();

      var mergedData = {};
      for (var k in existingData) {
        if (existingData.hasOwnProperty(k)) mergedData[k] = existingData[k];
      }
      mergedData.url = entityData.url;
      if (entityData.id !== undefined) mergedData.id = entityData.id;
      if (entityData.parentId !== undefined)
        mergedData.parentId = entityData.parentId;

      newContent = newContent.createEntity(ENTITY_TYPE, 'MUTABLE', mergedData);
      newEntityKey = newContent.getLastCreatedEntityKey();

      var entityKey = props.entityKey;
      var startKey = selection.getStartKey();
      var startOffset = selection.getStartOffset();
      var block = newContent.getBlockForKey(startKey);
      if (block) {
        var rangeStart = startOffset;
        var rangeEnd = startOffset + 1;
        while (
          rangeStart > 0 &&
          block.getEntityAt(rangeStart - 1) === entityKey
        ) {
          rangeStart--;
        }
        while (
          rangeEnd < block.getLength() &&
          block.getEntityAt(rangeEnd) === entityKey
        ) {
          rangeEnd++;
        }
        var rangeSelection = selection.merge({
          anchorKey: startKey,
          anchorOffset: rangeStart,
          focusKey: startKey,
          focusOffset: rangeEnd,
        });
        try {
          newContent = Modifier.applyEntity(
            newContent,
            rangeSelection,
            newEntityKey,
          );
        } catch (e) {
          console.warn(
            'draftail_text_utils StyledLinkSource: applyEntity range failed',
            e,
          );
        }
      }
    } else {
      // Check for existing TEXT_STYLE entity data in the selection
      // so that style properties (color, background, size) are preserved
      // when creating a new link on already-styled text.
      var existingStyleData = null;
      var startKey = selection.getStartKey();
      var endKey = selection.getEndKey();
      var startOffset = selection.getStartOffset();
      var endOffset = selection.getEndOffset();
      var inSelection = false;
      contentState.getBlockMap().forEach(function (block, blockKey) {
        if (blockKey === startKey) inSelection = true;
        if (!inSelection) return;
        var blockStart = blockKey === startKey ? startOffset : 0;
        var blockEnd = blockKey === endKey ? endOffset : block.getLength();
        for (var i = blockStart; i < blockEnd; i++) {
          var ek = block.getEntityAt(i);
          if (ek) {
            try {
              var ent = contentState.getEntity(ek);
              if (ent.getType() === ENTITY_TYPE || ent.getType() === 'LINK') {
                existingStyleData = ent.getData();
              }
            } catch (e) {
              // Entity not found
            }
          }
        }
        if (blockKey === endKey) inSelection = false;
      });

      var mergedEntityData = {};
      if (existingStyleData) {
        for (var k in existingStyleData) {
          if (existingStyleData.hasOwnProperty(k))
            mergedEntityData[k] = existingStyleData[k];
        }
      }
      for (var lk in entityData) {
        if (entityData.hasOwnProperty(lk))
          mergedEntityData[lk] = entityData[lk];
      }

      newContent = newContent.createEntity(
        ENTITY_TYPE,
        'MUTABLE',
        mergedEntityData,
      );
      newEntityKey = newContent.getLastCreatedEntityKey();

      if (
        chosenData.prefer_this_title_as_link_text ||
        selection.isCollapsed()
      ) {
        var text = chosenData.title || chosenData.url;
        newContent = Modifier.replaceText(
          newContent,
          selection,
          text,
          null,
          newEntityKey,
        );
      } else {
        var contentWithoutLink = Modifier.applyEntity(
          newContent,
          selection,
          null,
        );
        newContent = Modifier.applyEntity(
          contentWithoutLink,
          selection,
          newEntityKey,
        );
      }
    }

    var newState;
    try {
      newState = EditorState.push(editorState, newContent, 'apply-entity');
    } catch (e) {
      console.warn(
        'draftail_text_utils StyledLinkSource: EditorState.push failed',
        e,
      );
      newState = editorState;
    }

    this.workflow.close();
    onComplete(newState);
  };

  StyledLinkSource.prototype.onClose = function (e) {
    if (e) e.preventDefault();
    this.props.onClose();
  };

  window.draftail.registerPlugin(
    {
      type: 'LINK',
      source: StyledLinkSource,
    },
    'entityTypes',
  );
})();
