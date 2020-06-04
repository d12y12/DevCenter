#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import json
import string
from shutil import ignore_patterns, copy2
import devspace
from devspace.commands import DevSpaceCommand
from devspace.exceptions import UsageError
from devspace.utils.misc import arglist_to_dict, copytree, get_project_settings, get_host_ip, name_validator
from devspace.servers.gitmirror import GitMirror


class Command(DevSpaceCommand):

    requires_project = False

    def syntax(self):
        return "<project_name> [project_dir] [Options]"

    def short_desc(self):
        return "Create new project"

    def add_options(self, parser):
        DevSpaceCommand.add_options(self, parser)
        parser.add_option("--projectonly", dest="projectonly", action="store_true",
                          help="Create project without add any servers")
        parser.add_option("-e", "--extra", dest="spargs", action="append", default=[], metavar="NAME=VALUE",
                         help="additional information about author or version")

    def process_options(self, args, opts):
        DevSpaceCommand.process_options(self, args, opts)
        try:
            opts.spargs = arglist_to_dict(opts.spargs)
        except ValueError:
            raise UsageError("Invalid -e value, use -e NAME=VALUE", print_help=False)

    def run(self, args, opts):
        if len(args) not in (1, 2):
            raise UsageError()

        project_name = args[0]
        project_dir = args[0]

        if len(args) == 2:
            project_dir = args[1]
        project_dir = os.path.normpath(os.path.abspath(project_dir)).replace('\\','/')

        if not os.path.exists(project_dir):
            os.mkdir(project_dir)

        if os.path.exists(os.path.join(project_dir, 'devspace.json')):
            self.exitcode = 1
            print('Error: devspace.json already exists in %s' % os.path.abspath(project_dir))
            return

        if not name_validator(project_name):
            print("""name rules:
                - May only contain alphanumeric characters or hyphens.
                - Cannot have multiple consecutive hyphens.
                - Cannot begin or end with a hyphen.
                - Maximum is 10 characters.""")
            self.exitcode = 1
            return

        author = opts.spargs['author'] if opts.spargs and 'author' in opts.spargs else ""
        version = opts.spargs['version'] if opts.spargs and 'version' in opts.spargs else "1.0.0"

        if opts.projectonly:
            config = {
                "project": project_name,
                "author": author,
                "version": version,
                "project_dir": project_dir,
                "host": get_host_ip(),
                "servers": []
            }
            with open(os.path.join(project_dir, 'devspace.json'), 'w', encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            copy2(os.path.join(self.templates_dir, 'docker-compose.yaml'),
                  os.path.join(project_dir, 'docker-compose.yaml'))
            print("New DevSpace project %r, created in:" % (project_name))
            print("    %s\n" % os.path.abspath(project_dir))
        else:
            copy2(os.path.join(self.templates_dir, 'devspace.json'), os.path.join(project_dir, 'devspace.json'))
            copy2(os.path.join(self.templates_dir, 'docker-compose.yaml'),
                  os.path.join(project_dir, 'docker-compose.yaml'))
            with open(os.path.join(project_dir, 'devspace.json'), 'r', encoding="utf-8") as f:
                config = json.load(f)
            config['project'] = project_name
            config['author'] = author
            config['version'] = version
            config['project_dir'] = project_dir
            config['host'] = get_host_ip()
            config = json.loads(string.Template(json.dumps(config)).substitute(
                template_dir=os.path.normpath(self.templates_dir).replace('\\', '/')))
            with open(os.path.join(project_dir, 'devspace.json'), 'w', encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.settings.set_dict(json.dumps(config))
            print("New DevSpace project %r, created in:" % (project_name))
            print("    %s\n" % os.path.abspath(project_dir))
            print("You can start example server with:")
            print("    cd %s" % os.path.abspath(project_dir))
            print("    devspace render demo")
            print("    devspace run")

    @property
    def templates_dir(self):
        return self.settings['TEMPLATES_DIR'] or \
               os.path.join(devspace.__path__[0], 'templates')