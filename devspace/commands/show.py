#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint
import json
from devspace.commands import DevSpaceCommand
from devspace.exceptions import UsageError
from devspace.utils.misc import find_project_config


class Command(DevSpaceCommand):

    requires_project = True

    def syntax(self):
        return ""

    def short_desc(self):
        return "Show project information"

    def run(self, args, opts):
        if len(args) != 0:
            raise UsageError()

        conf_file = find_project_config()
        with open(conf_file, 'r', encoding="utf-8") as f:
            print(json.dumps(json.load(f), indent=2))
