import re
import os
import json
import string

import devspace
from devspace.commands import DevSpaceCommand
from devspace.exceptions import UsageError
from devspace.utils.misc import walk_modules
from devspace.servers import DevSpaceServer
import inspect


def _get_server_from_module(module_name, server_setting):
    server_name = list(server_setting.keys())[0]
    for module in walk_modules(module_name):
        for obj in vars(module).values():
            if inspect.isclass(obj) and \
                    issubclass(obj, DevSpaceServer) and \
                    obj.__module__ == module.__name__ and \
                    not obj == DevSpaceServer and \
                    server_setting[server_name]['type'] == obj.type:
                return obj(server_setting)


class Command(DevSpaceCommand):

    requires_project = True

    def syntax(self):
        return "[Options]"

    def short_desc(self):
        return "Render servers"

    def add_options(self, parser):
        DevSpaceCommand.add_options(self, parser)
        parser.add_option("-a", "--a", dest="render_all", action="store_true",
                          help="Render all servers")
        parser.add_option("-s", "--server", dest="server_name",
                         help="Render server by its name")

    def run(self, args, opts):
        if len(args) > 0:
            raise UsageError()

        if opts.render_all:
            print("render all server")
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