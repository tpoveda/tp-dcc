from __future__ import annotations

from collections import OrderedDict

from yaml.composer import Composer
from yaml.constructor import SafeConstructor
from yaml.emitter import Emitter
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.representer import SafeRepresenter
from yaml.resolver import Resolver
from yaml.scanner import Scanner
from yaml.serializer import Serializer


class UnsortableList(list):
    def sort(self, *args, **kwargs):
        pass


class UnsortableOrderedDict(OrderedDict):
    def items(self, *args, **kwargs):
        return UnsortableList(OrderedDict.items(self, *args, **kwargs))


class NoddleDumper(Emitter, Serializer, SafeRepresenter, Resolver):
    def __init__(
        self,
        stream,
        default_style=None,
        default_flow_style=False,
        canonical=None,
        indent=None,
        width=None,
        allow_unicode=None,
        line_break=None,
        encoding=None,
        explicit_start=None,
        explicit_end=None,
        version=None,
        tags=None,
        sort_keys=True,
    ):
        Emitter.__init__(
            self,
            stream,
            canonical=canonical,
            indent=indent,
            width=width,
            allow_unicode=allow_unicode,
            line_break=line_break,
        )
        Serializer.__init__(
            self,
            encoding=encoding,
            explicit_start=explicit_start,
            explicit_end=explicit_end,
            version=version,
            tags=tags,
        )
        SafeRepresenter.__init__(
            self, default_style=default_style, default_flow_style=default_flow_style, sort_keys=sort_keys
        )
        Resolver.__init__(self)


class NoddleLoader(Reader, Scanner, Parser, Composer, SafeConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        SafeConstructor.__init__(self)
        Resolver.__init__(self)


NoddleDumper.add_representer(UnsortableOrderedDict, NoddleDumper.represent_dict)
