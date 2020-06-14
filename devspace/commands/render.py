#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import json
import string
import devspace
from devspace.commands import DevSpaceCommand
from devspace.exceptions import UsageError
from devspace.utils.misc import walk_modules
from devspace.servers import DevSpaceServer
from devspace.utils.misc import get_host_ip
import inspect


def _get_server_from_module(module_name, server_name, project_setting):
    for module in walk_modules(module_name):
        for obj in vars(module).values():
            if inspect.isclass(obj) and \
                    issubclass(obj, DevSpaceServer) and \
                    obj.__module__ == module.__name__ and \
                    not obj == DevSpaceServer and \
                    server_name == obj.type:
                return obj(project_setting)


class Command(DevSpaceCommand):

    requires_project = True

    def syntax(self):
        return "[Options]"

    def short_desc(self):
        return "Render servers"

    def add_options(self, parser):
        DevSpaceCommand.add_options(self, parser)
        parser.add_option("--all", dest="render_all", action="store_true",
                          help="Render all servers")
        parser.add_option("--server", dest="server_name",
                          help="Render server by its name")
        parser.add_option("--host", dest="host", action="store_true",
                          help="Render project file host ip")

    def run(self, args, opts):
        if len(args) > 0:
            raise UsageError()

        if opts.render_all:
            print("render all server")
            return

        if opts.host:
            return

        print("render_server")
        # print(self.settings.attributes)
        server_name = opts.server_name
        servers = self.settings.get("servers")
        if not servers or server_name not in servers.keys():
            print("No servers found please check your project configuration file")
            self.exitcode = 1
            return
        server = _get_server_from_module('devspace.servers', server_name, self.settings)
        server.render()
        server.update_docker_compose()


    @property
    def templates_dir(self):
        return self.settings['TEMPLATES_DIR'] or \
               os.path.join(devspace.__path__[0], 'templates')
