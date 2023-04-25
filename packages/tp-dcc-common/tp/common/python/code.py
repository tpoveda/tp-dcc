#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modules that contains utility functions related with code analysis
"""

import sys
import ast
import string

from tp.common.python import helpers, fileio, path as path_utils


def get_ast_function_args(function_node):
    """
    Returns function arguments from the give AST function node
    :param function_node: ast function node
    :return: list(str)
    """

    found_args = list()

    if not function_node.args:
        return found_args

    defaults = function_node.args.defaults
    args = function_node.args.args
    args.reverse()
    defaults.reverse()
    index = 0
    for arg in args:
        name = arg.id
        if name == 'self':
            continue
        default_value = None
        if index < len(defaults):
            default_value = defaults[index]
        if default_value:
            value = None
            if isinstance(default_value, ast.Str):
                value = "'%s'" % default_value.s
            if isinstance(default_value, ast.Name):
                value = default_value.id
            if isinstance(default_value, ast.Num):
                value = default_value.n
            if value:
                found_args.append('{}={}'.format(name, value))
            else:
                found_args.append(name)
        else:
            found_args.append(name)
        index += 1
    found_args.reverse()

    return found_args


def get_ast_function_name_and_args(function_node):
    """
    Return function name from given AST node
    :param function_node: ast node
    :return: str
    """

    function_name = function_node.name
    found_args = get_ast_function_args(function_node)
    if found_args:
        found_args_name = string.join(found_args, ',')
    else:
        found_args_name = ''

    function_name += '({})'.format(found_args_name)

    return function_name


def get_ast_class_members(class_node, parents=None, skip_list=None):
    """
    Returns given class node members
    :param class_node: ast class node
    :param parents: list
    :param skip_list: bool
    :return: list(str)
    """

    parents = helpers.force_list(parents)
    skip_list = helpers.force_list(skip_list)

    class_functions = list()
    class_variables = list()
    visited_namespaces = dict()

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if skip_list and name in skip_list:
                continue
            skip_list.append(name)
            if name in visited_namespaces:
                continue
            name_args = get_ast_function_name_and_args(node)
            if name_args.startswith('_'):
                continue
            name_args = name_args.replace('self,', '')
            class_functions.append(name_args)
            visited_namespaces[name] = None
        elif isinstance(node, ast.Expr):
            # Gets documentation
            pass
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if target.id in visited_namespaces:
                    continue
                if hasattr(node.value, 's'):
                    class_variables.append("{} = '{}'".format(target.id, node.value.s))
                elif hasattr(node.value, 'n'):
                    class_variables.append('{} = {}'.format(target.id, node.value.n))
                elif hasattr(node.value, 'elts'):
                    class_variables.append('{} = {}'.format(target.id, node.value.elts))
                else:
                    class_variables.append(target.id)
                visited_namespaces[target.id] = None

    found_parent_functions = list()
    found_parent_variables = list()
    for parent in parents:
        parent_functions, parent_variables = get_ast_class_members(parent, skip_list=skip_list)
        found_parent_functions += parent_functions
        found_parent_variables += parent_variables

    found_parent_functions += class_functions
    found_parent_variables += class_variables

    return found_parent_functions, found_parent_variables


def get_ast_class_sub_functions(module_path, class_name):
    """
    Returns list of sub functions for the given class
    :param module_path: str
    :param class_name: str
    :return: list(str)
    """

    defined, defined_dict = get_defined_classes(module_path)
    if not defined:
        return

    if class_name in defined:
        class_node = defined_dict[class_name]
        parents = list()
        bases = class_node.bases
        while bases:
            temp_bases = bases
            find_bases = list()
            for base in temp_bases:
                class_name = None
                if hasattr(base, 'id'):
                    class_name = base.id
                if class_name and class_name in defined_dict:
                    parents.append(defined_dict[class_name])
                    sub_bases = parents[-1].bases
                    if sub_bases:
                        find_bases += sub_bases
            bases = find_bases

        functions, variables = get_ast_class_members(class_node, parents)

        return functions, variables


def get_ast_assignment(text, line_number):
    text = str(text)
    if not text:
        return

    ast_tree = None
    try:
        ast_tree = ast.parse(text, 'string', 'exec')
    except Exception:
        if not ast_tree:
            return

    line_assign_dict = dict()
    value = None

    for node in ast.walk(ast_tree):
        if hasattr(node, 'lineno'):
            current_line_number = node.lineno
            if current_line_number <= line_number:
                if isinstance(node, ast.ImportFrom):
                    for name in node.names:
                        full_name = node.module + '.' + name.name
                        value = ['import', full_name]
                        if not name.asname:
                            line_assign_dict[name.name] = value
                        else:
                            line_assign_dict[name.asname] = ['import', full_name]
                elif isinstance(node, ast.Assign):
                    targets = list()
                    for target in node.targets:
                        if hasattr(target, 'id'):
                            targets.append(target.id)
                    if hasattr(node.value, 'id'):
                        value = node.value.id
                    if hasattr(node.value, 'func'):
                        value = list()
                        if hasattr(node.value.func, 'value'):
                            if hasattr(node.value.func.value, 'id'):
                                value.append(node.value.func.value.id)
                                value.append(node.value.func.attr)

                    if targets:
                        for target in targets:
                            if value:
                                line_assign_dict[target] = value

            if current_line_number > line_number:
                continue

    return line_assign_dict


def get_package_path_from_name(module_name, return_module_path=False):
    """
    Returns package path from given package name
    :param module_name: str, name of the module we want to retrieve path of
    :param return_module_path: bool
    :return: str
    """

    split_name = module_name.split('.')
    if len(split_name) > 1:
        sub_path = string.join(split_name[:-1], '/')
    else:
        sub_path = module_name

    paths = sys.path

    found_path = None
    for path in paths:
        test_path = path_utils.join_path(path, sub_path)
        if path_utils.is_dir(test_path):
            found_path = path

    if not found_path:
        return None

    test_path = found_path
    good_path = ''
    index = 0

    for name in split_name:
        if index == len(split_name) - 1:
            if return_module_path:
                good_path = path_utils.join_path(good_path, '{}.py'.format(name))
                break

        test_path = path_utils.join_path(test_path, name)
        if not path_utils.is_dir(test_path):
            continue
        files = fileio.get_files(test_path)
        if '__init__.py' in files:
            good_path = test_path
        else:
            return None

        index += 1

    return good_path


def get_line_imports(lines):
    """
    Returns all import lines in the given lines
    :param lines: list(str)
    :return: dict(str, str)
    """

    # TODO: Replace this function by AST implementation

    module_dict = dict()

    for line in lines:
        line = str(line)
        split_line = line.split()
        split_line_count = len(split_line)
        for i in range(split_line_count):
            module_prefix = ''
            if split_line[i] == 'import':
                if i > 1:
                    if split_line[i - 2] == 'from':
                        module_prefix = split_line[i - 1]
                if i < split_line_count - 1:
                    module = split_line[i + 1]
                    namespace = module
                    if module_prefix:
                        module = '{}.{}'.format(module_prefix, module)
                    module_path = get_package_path_from_name(module, return_module_path=True)
                    module_dict[namespace] = module_path

    return module_dict


def get_defined(module_path, name_only=False):
    """
    Get classes and definitions from the text of a module
    """

    file_text = fileio.get_file_text(module_path)
    if not file_text:
        return

    functions = list()
    classes = list()

    ast_tree = ast.parse(file_text, 'string', 'exec')
    for node in ast_tree.body:
        if isinstance(node, ast.FunctionDef):
            function_name = node.name
            if not name_only:
                function_name = get_ast_function_name_and_args(node)
            functions.append(function_name)
        if isinstance(node, ast.ClassDef):
            class_name = node.name + '()'
            for sub_node in node.body:
                if isinstance(sub_node, ast.FunctionDef):
                    if sub_node.name == '__init__':
                        found_args = get_ast_function_args(sub_node)
                        if found_args:
                            found_args_name = string.join(found_args, ',')
                        else:
                            found_args_name = ''
                        class_name = '{}({})'.format(node.name, found_args_name)
            classes.append(class_name)

    classes.sort()
    functions.sort()
    defined = classes + functions

    return defined


def get_defined_classes(module_path):
    """
    Returns classes of the given module
    :param module_path: str
    :return: list(str)
    """

    file_text = fileio.get_text(module_path)

    defined = list()
    defined_dict = dict()

    if not file_text:
        return None, None

    ast_tree = ast.parse(file_text)
    for node in ast_tree.body:
        if isinstance(node, ast.ClassDef):
            defined.append(node.name)
            defined_dict[node.name] = node

    return defined, defined_dict
