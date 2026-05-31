(function () {
  var dt = (window.DraftailTextUtils = window.DraftailTextUtils || {});

  dt._savedSelection = null;

  dt.saveSelection = function (getEditorState) {
    var selection = getEditorState().getSelection();
    if (selection && !selection.isCollapsed()) {
      dt._savedSelection = selection;
    }
  };

  dt.restoreSelection = function (editorState) {
    if (dt._savedSelection && !dt._savedSelection.isCollapsed()) {
      return window.DraftJS.EditorState.forceSelection(
        editorState,
        dt._savedSelection,
      );
    }
    return editorState;
  };

  dt.removeEntity = function (editorState, entityType) {
    var Modifier = window.DraftJS.Modifier;
    var EditorState = window.DraftJS.EditorState;
    var selection = editorState.getSelection();
    if (!selection.getHasFocus() || selection.isCollapsed()) return editorState;

    var contentState = editorState.getCurrentContent();
    var startKey = selection.getStartKey();
    var endKey = selection.getEndKey();
    var startOffset = selection.getStartOffset();
    var endOffset = selection.getEndOffset();

    var updatedContent = contentState;
    var inSelection = false;

    contentState.getBlockMap().forEach(function (block, blockKey) {
      if (blockKey === startKey) inSelection = true;
      if (!inSelection) return;

      var blockStart = blockKey === startKey ? startOffset : 0;
      var blockEnd = blockKey === endKey ? endOffset : block.getLength();

      var i = blockStart;
      while (i < blockEnd) {
        var entityKey = block.getEntityAt(i);
        if (entityKey) {
          try {
            var entity = contentState.getEntity(entityKey);
            if (entity.getType() === entityType) {
              var rangeEnd = i + 1;
              while (
                rangeEnd < blockEnd &&
                block.getEntityAt(rangeEnd) === entityKey
              ) {
                rangeEnd++;
              }

              var rangeSelection = selection.merge({
                anchorKey: blockKey,
                anchorOffset: i,
                focusKey: blockKey,
                focusOffset: rangeEnd,
              });
              updatedContent = Modifier.applyEntity(
                updatedContent,
                rangeSelection,
                null,
              );

              i = rangeEnd;
              continue;
            }
          } catch (e) {
            // Entity may have been deleted
          }
        }
        i++;
      }

      if (blockKey === endKey) inSelection = false;
    });

    try {
      return EditorState.push(editorState, updatedContent, 'apply-entity');
    } catch (e) {
      return editorState;
    }
  };

  dt.getActiveEntityData = function (editorState, entityType, dataKey) {
    var selection = editorState.getSelection();
    if (!selection.getHasFocus()) return null;

    var contentState = editorState.getCurrentContent();
    var startKey = selection.getStartKey();
    var startOffset = selection.getStartOffset();
    var blockWithEntityAt = contentState.getBlockForKey(startKey);
    if (!blockWithEntityAt) return null;

    var entityKey = blockWithEntityAt.getEntityAt(startOffset);
    if (entityKey) {
      try {
        var entity = contentState.getEntity(entityKey);
        if (entity.getType() === entityType) {
          return entity.getData()[dataKey];
        }
      } catch (e) {
        // Entity not found
      }
    }

    if (selection.isCollapsed() && startOffset > 0) {
      entityKey = blockWithEntityAt.getEntityAt(startOffset - 1);
      if (entityKey) {
        try {
          var entity = contentState.getEntity(entityKey);
          if (entity.getType() === entityType) {
            return entity.getData()[dataKey];
          }
        } catch (e) {
          // Entity not found
        }
      }
    }

    return null;
  };

  dt.parseControl = function (type) {
    return JSON.parse(
      document.getElementById('draftail-plugin-control-' + type).textContent,
    );
  };

  dt.clickOutsideGuard = function (ref, event) {
    return ref.current && !ref.current.contains(event.target);
  };

  dt.mergeStyleEntity = function (editorState, entityType, data) {
    var Modifier = window.DraftJS.Modifier;
    var EditorState = window.DraftJS.EditorState;
    var selection = editorState.getSelection();
    if (!selection.getHasFocus() || selection.isCollapsed()) return editorState;

    var contentState = editorState.getCurrentContent();
    var startKey = selection.getStartKey();
    var endKey = selection.getEndKey();
    var startOffset = selection.getStartOffset();
    var endOffset = selection.getEndOffset();

    var hasOtherEntity = false;
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
            var eType = ent.getType();
            if (eType !== entityType && eType !== 'LINK') {
              hasOtherEntity = true;
            }
          } catch (e) {
            // Entity not found
          }
        }
      }

      if (blockKey === endKey) inSelection = false;
    });

    if (hasOtherEntity) return editorState;

    var existingData = null;
    var existingKey = null;
    var uniformSelection = true;
    var firstKey = null;
    inSelection = false;

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
            var eType = ent.getType();
            if (eType === entityType || eType === 'LINK') {
              if (existingKey === null) {
                existingKey = ek;
                existingData = ent.getData();
                firstKey = ek;
              } else if (ek !== firstKey) {
                uniformSelection = false;
              }
            } else {
              uniformSelection = false;
            }
          } catch (e) {
            uniformSelection = false;
          }
        } else {
          uniformSelection = false;
        }
      }

      if (blockKey === endKey) inSelection = false;
    });

    var updatedContent = contentState;

    if (existingData) {
      var mergedData = {};
      for (var k in existingData) {
        if (existingData.hasOwnProperty(k)) mergedData[k] = existingData[k];
      }
      for (var dk in data) {
        if (data.hasOwnProperty(dk)) mergedData[dk] = data[dk];
      }
      mergedData.url = mergedData.url || '';
      updatedContent = updatedContent.createEntity(
        entityType,
        'MUTABLE',
        mergedData,
      );
      updatedContent = Modifier.applyEntity(
        updatedContent,
        selection,
        updatedContent.getLastCreatedEntityKey(),
      );
    } else {
      data.url = '';
      updatedContent = updatedContent.createEntity(entityType, 'MUTABLE', data);
      updatedContent = Modifier.applyEntity(
        updatedContent,
        selection,
        updatedContent.getLastCreatedEntityKey(),
      );
    }

    try {
      return EditorState.push(editorState, updatedContent, 'apply-entity');
    } catch (e) {
      return editorState;
    }
  };

  dt.removeStyleProperty = function (editorState, entityType, propertyKey) {
    var Modifier = window.DraftJS.Modifier;
    var EditorState = window.DraftJS.EditorState;
    var selection = editorState.getSelection();
    if (!selection.getHasFocus() || selection.isCollapsed()) return editorState;

    var contentState = editorState.getCurrentContent();
    var startKey = selection.getStartKey();
    var startOffset = selection.getStartOffset();
    var block = contentState.getBlockForKey(startKey);
    if (!block) return editorState;

    for (var offset = startOffset; offset >= 0; offset--) {
      var entityKey = block.getEntityAt(offset);
      if (entityKey) {
        try {
          var entity = contentState.getEntity(entityKey);
          if (entity.getType() === entityType) {
            var entityData = entity.getData();
            var newData = {};
            var hasOtherStyle = false;
            var hasLinkData = false;
            for (var k in entityData) {
              if (entityData.hasOwnProperty(k) && k !== propertyKey) {
                newData[k] = entityData[k];
                if (k === 'url' || k === 'id' || k === 'parentId') {
                  hasLinkData = true;
                } else {
                  hasOtherStyle = true;
                }
              }
            }

            // Find the full extent of the entity around the cursor
            var rangeStart = offset;
            var rangeEnd = offset + 1;
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

            if (hasOtherStyle) {
              // Still have other style properties — keep as TEXT_STYLE
              contentState = contentState.createEntity(
                entityType,
                'MUTABLE',
                newData,
              );
              contentState = Modifier.applyEntity(
                contentState,
                rangeSelection,
                contentState.getLastCreatedEntityKey(),
              );
            } else if (hasLinkData) {
              // No style properties left, but still has link data —
              // keep TEXT_STYLE entity with just the link data
              contentState = contentState.createEntity(
                entityType,
                'MUTABLE',
                newData,
              );
              contentState = Modifier.applyEntity(
                contentState,
                rangeSelection,
                contentState.getLastCreatedEntityKey(),
              );
            } else {
              // No style properties and no link data — remove the entity
              contentState = Modifier.applyEntity(
                contentState,
                rangeSelection,
                null,
              );
            }
            break;
          }
        } catch (e) {
          continue;
        }
      }
    }

    try {
      return EditorState.push(editorState, contentState, 'apply-entity');
    } catch (e) {
      return editorState;
    }
  };
})();
