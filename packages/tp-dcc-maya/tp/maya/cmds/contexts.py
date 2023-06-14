#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with custom Maya Python contexts
"""

import contextlib
from typing import List

import maya.mel as mel
import maya.cmds as cmds

from tp.core import log
from tp.maya.cmds import helpers, exceptions, nodeeditor

logger = log.tpLogger


@contextlib.contextmanager
def undo_chunk_context(name=None):
    """
    Enables undo functionality during the context execution.
    """

    try:
        cmds.undoInfo(openChunk=True, chunkName=name or '')
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


@contextlib.contextmanager
def maya_no_undo():
    """
    Disable undo functionality during the context
    """

    try:
        cmds.undoInfo(stateWithoutFlush=False)
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


@contextlib.contextmanager
def suspend_refresh_context():
    """
    Suspends viewport refresh during the context execution
    """

    try:
        cmds.refresh(suspend=True)
        yield
    finally:
        cmds.refresh(suspend=False)


@contextlib.contextmanager
def disable_viewport_context():
    """
    Disables viewport during the context execution.
    """

    maya_version = helpers.maya_version()
    try:
        cmds.refresh(suspend=True)
        mel.eval('setTimeSliderVisible 0;')
        if maya_version >= 2016:
            eval_mode = cmds.evaluationManager(query=True, mode=True)
            cmds.evaluationManager(mode='off')
        yield
    finally:
        cmds.refresh(suspend=False)
        mel.eval('setTimeSliderVisible 1;')
        if maya_version >= 2016:
            cmds.evaluationManager(mode=eval_mode[0])


@contextlib.contextmanager
def no_panel_refresh_context():
    """
    Disable all controlled panel refresh during the context execution
    """

    controls = list()
    for panel in cmds.lsUI(panels=True, long=True):
        control = cmds.panel(panel, query=True, control=True)
        if not control:
            continue
        if not cmds.layout(control, query=True, visible=True):
            continue
        controls.append(control)

    try:
        for control in controls:
            cmds.layout(control, edit=True, manage=False)
        yield
    finally:
        for control in controls:
            try:
                cmds.layout(control, edit=True, manage=True)
            except RuntimeError:
                logger.warning('Cannot manage control {}'.format(control))


@contextlib.contextmanager
def no_refresh_context():
    """
    Disables Maya UIs updates during the context execution

    ..note:: This only disables the main pain and will sometimes still trigger updates in torn of panels.
    """

    pane = helpers.mel_global_variable_value('gMainPane')
    state = cmds.paneLayout(pane, q=1, manage=1)
    cmds.paneLayout(pane, e=1, manage=False)
    try:
        yield
    finally:
        cmds.paneLayout(pane, e=1, manage=state)


@contextlib.contextmanager
def isolated_nodes(nodes: List[str], panel: str):
    """
    Context Manager for isolating nodes in Maya model panel.

    :param List[str] nodes: list of node names to isolate.
    :param str panel: Maya model panel name.
    """

    cmds.isolateSelect(panel, state=True)
    for obj in nodes:
        cmds.isolateSelect(panel, addDagObject=obj)
    yield
    cmds.isolateSelect(panel, state=False)


@contextlib.contextmanager
def isolate_views_context():
    """
    Isolates selection with nothing selected for all viewports.
    This speeds up any process that causes the viewport to refresh, such as baking or changing time.
    """

    def _isolate(state):
        cmds.select(clear=True)
        for model_panel in model_panels:
            if model_panel not in already_isolated:
                cmds.isolateSelect(model_panel, state=state)

    maya_version = helpers.float_version()
    if maya_version >= 2016.5:
        if not cmds.ogs(query=True, pause=True):
            cmds.ogs(pause=True)
    else:
        selection = cmds.ls(sl=True)
        model_panels = cmds.getPanel(type='modelPanel')
        already_isolated = list()
        for panel_name in model_panels:
            if cmds.isolateSelect(panel_name, query=True, state=True):
                already_isolated.append(panel_name)
        _isolate(True)
        cmds.select(clear=True)

    reset_auto_key = cmds.autoKeyframe(query=True, state=True)
    cmds.autoKeyframe(state=False)

    try:
        yield
    finally:
        cmds.autoKeyframe(state=reset_auto_key)
        if maya_version >= 2016.5:
            if cmds.ogs(query=True, pause=True):
                cmds.ogs(pause=True)
        else:
            if selection:
                try:
                    cmds.select(selection)
                except Exception:
                    pass
            _isolate(False)


@contextlib.contextmanager
def disable_cycle_check_warnings_context():
    """
    Disables Cycle Check warnings during the context execution

    ..note:: This only disables the main pain and will sometimes still trigger updates in torn of panels.
    """

    current_evaluation = cmds.cycleCheck(evaluation=True, query=True)
    try:
        cmds.cycleCheck(evaluation=False)
        yield
    finally:
        cmds.cycleCheck(evaluation=current_evaluation)


@contextlib.contextmanager
def namespace_context(namespace):
    """
    Python context that sets the given namespace as the active namespace and after yielding the function restores
    the previous namespace.

    :param str namespace: namespace name to set as active one.

    ..note:: if the give namespace does not exist, it will be created automatically.
    """

    # some characters are illegal for namespaces
    namespace = namespace.replace('.', '_')
    if namespace != ':' and namespace.endswith(':'):
        namespace = namespace[:-1]

    current_namespace = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
    existing_namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True, absoluteName=True)
    if current_namespace != namespace and namespace not in existing_namespaces and namespace != ':':
        try:
            namespace = cmds.namespace(add=namespace)
        except RuntimeError:
            logger.error('Failed to create namespace: {}, existing namespaces: {}'.format(
                namespace, existing_namespaces), exc_info=True)
            cmds.namespace(setNamespace=current_namespace)
            raise
    cmds.namespace(setNamespace=namespace)
    try:
        yield
    finally:
        cmds.namespace(setNamespace=current_namespace)


@contextlib.contextmanager
def unlock_attribute_context(node, attribute_name):
    """
    Maya context that allows to force unlock of an attribute before executing a function and recover its
    original lock status after the function is executed.

    :param str node: node to unlock.
    :param str attribute: attribute name to unlock.
    """

    is_locked = not cmds.getAttr('{}.{}'.format(node, attribute_name), settable=True)
    if is_locked:
        cmds.setAttr('{}.{}'.format(node, attribute_name), lock=False)
    try:
        yield
    finally:
        if is_locked:
            cmds.setAttr('{}.{}'.format(node, attribute_name), lock=True)


@contextlib.contextmanager
def unlock_node_context(node):
    """
    Maya context that allows to force unlock of a node before executing a function and recover its original
    lock state after the function is executed.

    :param pm.PyNode node: node to unlock.
    """

    set_locked = False
    if node and cmds.objExists(node):
        if node.isLocked():
            if node.isReferenced():
                raise exceptions.ReferenceObjectError(
                    'Unable to unlock a referenced node: {}'.format(node.fullPathName()))
            node.unlock()
            set_locked = True
    try:
        yield
    finally:
        if node and cmds.objExists(node) and set_locked:
            node.lock()


@contextlib.contextmanager
def maintained_selection_context():
    """
    Maintain selection during context
    Example:
        >>> scene = cmds.file(new=True, force=True)
        >>> node = cmds.createNode('transform', name='newGroup')
        >>> cmds.select('persp')
        >>> with maintained_selection_context():
        ...     cmds.select(node, replace=True)
        >>> node in cmds.ls(selection=True)
        False
    """

    previous_selection = cmds.ls(selection=True)
    try:
        yield
    finally:
        if previous_selection:
            valid_selection = [node for node in previous_selection if node and cmds.objExists(node)]
            if valid_selection:
                cmds.select(valid_selection, replace=True, noExpand=True)
        else:
            cmds.select(clear=True)


@contextlib.contextmanager
def maintain_time_context():
    """
    Context manager that preserves the time after the context.
    """

    current_time = cmds.currentTime(query=True)
    try:
        yield
    finally:
        cmds.currentTime(current_time, edit=True)


@contextlib.contextmanager
def disable_node_editor_add_node_context():
    """
    Context manager which disables the current node editors "Add to graph on create", which slows Maya down a lot.
    """

    editor = nodeeditor.primary_node_editor()
    state = False
    editor_wrapper = None
    if editor:
        editor_wrapper = nodeeditor.NodeEditorWrapper(editor)
        state = editor_wrapper.add_nodes_on_create()
        if state:
            editor_wrapper.set_add_nodes_on_create(False)
    yield
    if state:
        editor_wrapper.set_add_nodes_on_create(state)
