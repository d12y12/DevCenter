# -*- coding: UTF-8 -*-
import os
import json
import string
from importlib import import_module
from devspace.utils.misc import walk_modules
from devspace.exceptions import ConfigurationError


class Settings:
    def __init__(self, values=None):
        self.attributes = {}
        self.set_module('devspace.settings')
        self.update(values)

    def __getitem__(self, name):
        if name not in self:
            return None
        return self.attributes[name]

    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, name):
        return name in self.attributes

    def __delitem__(self, name):
        del self.attributes[name]

    def __iter__(self):
        return iter(self.attributes)

    def __len__(self):
        return len(self.attributes)

    def set_module(self, path):
        for module in walk_modules(path):
            if isinstance(module, str):
                module = import_module(module)
            for key in dir(module):
                if key.isupper():
                    self.set(key, getattr(module, key))

    def set(self, name, value):
        self.attributes[name] = value

    def set_dict(self, values):
        self.update(values)

    def update(self, values):
        if isinstance(values, str):
            values = json.loads(values)
            if values is not None:
                for name, value in values.items():
                    self.set(name, value)
                    if name == "project":
                        if isinstance(value['path'], str):
                            project_dir = value['path']
                            self.attributes['SHARED_WEB'] = os.path.normpath(
                                string.Template(self.attributes['SHARED_WEB']).substitute(PROJECT_DIR=project_dir)).\
                                replace('\\', '/')
                            self.attributes['SHARED_DATA'] = os.path.normpath(
                                string.Template(self.attributes['SHARED_DATA']).substitute(PROJECT_DIR=project_dir)). \
                                replace('\\', '/')
                            self.attributes['SHARED_LOG'] = os.path.normpath(
                                string.Template(self.attributes['SHARED_LOG']).substitute(PROJECT_DIR=project_dir)). \
                                replace('\\', '/')
                            self.attributes['CGIT_STATICS'] = os.path.normpath(
                                string.Template(self.attributes['CGIT_STATICS']).substitute(PROJECT_DIR=project_dir)). \
                                replace('\\', '/')

    def get(self, name, default=None):
        return self[name] if self[name] is not None else default

    def get_bool(self, name, default=False):
        got = self.get(name, default)
        try:
            return bool(int(got))
        except ValueError:
            if got in ("True", "true"):
                return True
            if got in ("False", "false"):
                return False
            raise ConfigurationError("Supported values for boolean settings "
                                     "are 0/1, True/False, '0'/'1', "
                                     "'True'/'False' and 'true'/'false'")

    def get_dict(self, name, default=None):
        value = self.get(name, default or {})
        if isinstance(value, str):
            value = json.loads(value)
        return dict(value)

    def delete(self, name):
        del self.attributes[name]
