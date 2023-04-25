# :coding: utf-8
# :copyright: Copyright (c) 2013 Martin Pengelly-Phillips
# :license: See LICENSE.txt.
from __future__ import absolute_import

import os
import sys
import uuid

from tpDcc.libs.nameit.externals.lucidity._version import __version__
from tpDcc.libs.nameit.externals.lucidity.template import Template, Resolver
from tpDcc.libs.nameit.externals.lucidity.error import ParseError, FormatError, NotFound


def discover_templates(paths=None, recursive=True):
    '''Search *paths* for mount points and load templates from them.

    *paths* should be a list of filesystem paths to search for mount points.
    If not specified will try to use value from environment variable
    :envvar:`LUCIDITY_TEMPLATE_PATH`.

    A mount point is a Python file that defines a 'register' function. The
    function should return a list of instantiated
    :py:class:`~lucidity.template.Template` objects.

    If *recursive* is True (the default) then all directories under a path
    will also be searched.

    '''
    templates = []

    if paths is None:
        paths = os.environ.get('LUCIDITY_TEMPLATE_PATH', '').split(os.pathsep)

    for path in paths:
        for base, directories, filenames in os.walk(path):
            for filename in filenames:
                _, extension = os.path.splitext(filename)
                if extension != '.py':
                    continue

                module_path = os.path.join(base, filename)
                module_name = uuid.uuid4().hex
                module = load_module_from_file(module_name, module_path)
                try:
                    registered = module.register()
                except AttributeError:
                    pass
                else:
                    if registered:
                        templates.extend(registered)

            if not recursive:
                del directories[:]

    return templates


def parse(path, templates):
    '''Parse *path* against *templates*.

    *path* should be a string to parse.

    *templates* should be a list of :py:class:`~lucidity.template.Template`
    instances in the order that they should be tried.

    Return ``(data, template)`` from first successful parse.

    Raise :py:class:`~lucidity.error.ParseError` if *path* is not
    parseable by any of the supplied *templates*.

    '''
    for template in templates:
        try:
            data = template.parse(path)
        except ParseError:
            continue
        else:
            return (data, template)

    raise ParseError(
        'Path {0!r} did not match any of the supplied template patterns.'
        .format(path)
    )


def format(data, templates):  # @ReservedAssignment
    '''Format *data* using *templates*.

    *data* should be a dictionary of data to format into a path.

    *templates* should be a list of :py:class:`~lucidity.template.Template`
    instances in the order that they should be tried.

    Return ``(path, template)`` from first successful format.

    Raise :py:class:`~lucidity.error.FormatError` if *data* is not
    formattable by any of the supplied *templates*.


    '''
    for template in templates:
        try:
            path = template.format(data)
        except FormatError:
            continue
        else:
            return (path, template)

    raise FormatError(
        'Data {0!r} was not formattable by any of the supplied templates.'
        .format(data)
    )


def get_template(name, templates):
    '''Retrieve a template from *templates* by *name*.

    Raise :py:exc:`~lucidity.error.NotFound` if no matching template with
    *name* found in *templates*.

    '''
    for template in templates:
        if template.name == name:
            return template

    raise NotFound(
        '{0} template not found in specified templates.'.format(name)
    )


def load_module_from_file(module_name, module_path):
    """Loads a python module from the path of the corresponding file.
    Args:
        module_name (str): namespace where the python module will be loaded,
            e.g. ``foo.bar``
        module_path (str): path of the python file containing the module
    Returns:
        A valid module object
    Raises:
        ImportError: when the module can't be loaded
        FileNotFoundError: when module_path doesn't exist
    """
    if sys.version_info[0] == 3 and sys.version_info[1] >= 5:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif sys.version_info[0] == 3 and sys.version_info[1] < 5:
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader(module_name, module_path)
        module = loader.load_module()
    elif sys.version_info[0] == 2:
        import imp
        module = imp.load_source(module_name, module_path)
    return module
