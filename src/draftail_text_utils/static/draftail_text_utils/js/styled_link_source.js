(function () {
  if (!window.draftail) return;

  var LinkModalWorkflowSource = window.draftail.LinkModalWorkflowSource;
  if (!LinkModalWorkflowSource) return;

  var ENTITY_TYPE = 'TEXT_STYLE';

  function getStyleData(contentState, selection) {
    var startKey = selection.getStartKey();
    var endKey = selection.getEndKey();
    var startOffset = selection.getStartOffset();
    var endOffset = selection.getEndOffset();
    var inSelection = false;
    var result = null;

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
            if (ent.getType() === ENTITY_TYPE) {
              result = ent.getData();
            }
          } catch (e) {
            // Entity not found
          }
        }
      }
      if (blockKey === endKey) inSelection = false;
    });

    return result;
  }

  class StyledLinkSource extends LinkModalWorkflowSource {
    onChosen(chosenData) {
      var Modifier = window.DraftJS.Modifier;
      var EditorState = window.DraftJS.EditorState;
      var props = this.props;
      var editorState = props.editorState;
      var entity = props.entity;
      var onComplete = props.onComplete;

      var contentState = editorState.getCurrentContent();
      var selection = editorState.getSelection();
      var entityData = this.filterEntityData(chosenData);

      // Handle remove link: when no URL and no ID, preserve style data
      // but remove link data from the entity
      if (!entityData.url && !entityData.id) {
        var mergedData = {};
        if (entity) {
          var existingData = entity.getData();
          for (var k in existingData) {
            if (existingData.hasOwnProperty(k)) mergedData[k] = existingData[k];
          }
        }
        // Clear link data but keep style data
        mergedData.url = '';
        delete mergedData.id;
        delete mergedData.parentId;

        // Check if there are any style properties left
        var hasStyles =
          mergedData.color || mergedData.backgroundColor || mergedData.size;

        if (hasStyles) {
          // Preserve as a TEXT_STYLE entity with styles only (no link)
          var newContent = contentState.createEntity(
            ENTITY_TYPE,
            'MUTABLE',
            mergedData,
          );
          newContent = Modifier.applyEntity(
            newContent,
            selection,
            newContent.getLastCreatedEntityKey(),
          );
          var newState = EditorState.push(
            editorState,
            newContent,
            'apply-entity',
          );
          this.workflow.close();
          onComplete(newState);
        } else {
          // No styles — remove the entity entirely
          var contentWithoutLink = Modifier.applyEntity(
            contentState,
            selection,
            null,
          );
          var newState = EditorState.push(
            editorState,
            contentWithoutLink,
            'apply-entity',
          );
          this.workflow.close();
          onComplete(newState);
        }
        return;
      }

      var mergedData = {};
      if (entity) {
        var existingData = entity.getData();
        for (var k in existingData) {
          if (existingData.hasOwnProperty(k)) mergedData[k] = existingData[k];
        }
      }
      var styleData = getStyleData(contentState, selection);
      if (styleData) {
        for (var k in styleData) {
          if (styleData.hasOwnProperty(k)) mergedData[k] = styleData[k];
        }
      }
      mergedData.url = entityData.url;
      if (entityData.id !== undefined) mergedData.id = entityData.id;
      if (entityData.parentId !== undefined)
        mergedData.parentId = entityData.parentId;

      var newContent = contentState.createEntity(
        ENTITY_TYPE,
        'MUTABLE',
        mergedData,
      );
      var newEntityKey = newContent.getLastCreatedEntityKey();

      if (entity) {
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
          newContent = Modifier.applyEntity(
            newContent,
            rangeSelection,
            newEntityKey,
          );
        }
      } else {
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

      var newState = EditorState.push(editorState, newContent, 'apply-entity');

      this.workflow.close();
      onComplete(newState);
    }
  }

  window.draftail.registerPlugin(
    {
      type: 'LINK',
      source: StyledLinkSource,
    },
    'entityTypes',
  );

  window.draftail.StyledLinkSource = StyledLinkSource;
})();
