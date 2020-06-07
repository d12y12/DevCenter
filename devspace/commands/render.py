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


def _get_server_from_module(module_name, server_setting):
    server_name = list(server_setting.keys())[0]
    for module in walk_modules(module_name):
        for obj in vars(module).values():
            if inspect.isclass(obj) and \
                    issubclass(obj, DevSpaceServer) and \
                    obj.__module__ == module.__name__ and \
                    not obj == DevSpaceServer and \
                    server_setting[server_name]['type'].split('-')[0] == obj.type:
                return obj(server_setting)


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
            project_dir = self.settings.get('project_dir', '')
            if not project_dir:
                raise UsageError('Not in project')
            with open(os.path.join(project_dir, 'devspace.json'), 'r', encoding="utf-8") as f:
                config = json.load(f)
            config['host'] = get_host_ip()
            with open(os.path.join(project_dir, 'devspace.json'), 'w', encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.settings.set_dict(json.dumps(config))
            return

        server_name = opts.server_name
        servers = self.settings.get("servers")
        if not servers:
            print("No servers found please check your project configuration file")
            self.exitcode = 1
            return
        server_to_render = {}
        for name, server_setting in servers.items():
            if name == server_name:
                server_to_render = {
                    name: server_setting,
                }
                break
        if not server_to_render:
            print("Server name not found")
            self.exitcode = 1
            return
        server = _get_server_from_module('devspace.servers', server_to_render)
        server.render()
        server.update_docker_compose()


    @property
    def templates_dir(self):
        return self.settings['TEMPLATES_DIR'] or \
               os.path.join(devspace.__path__[0], 'templates')
