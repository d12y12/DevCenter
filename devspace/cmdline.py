#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import optparse
import inspect
import pkg_resources

import devspace
from devspace.commands import DevSpaceCommand
from devspace.exceptions import UsageError
from devspace.settings import Settings
from devspace.utils.misc import walk_modules, inside_project, get_project_settings
# from scrapy.utils.python import garbage_collect


def _iter_command_classes(module_name):
    for module in walk_modules(module_name):
        for obj in vars(module).values():
            if inspect.isclass(obj) and \
                    issubclass(obj, DevSpaceCommand) and \
                    obj.__module__ == module.__name__ and \
                    not obj == DevSpaceCommand:
                yield obj


def _get_commands_from_module(module, inproject):
    d = {}
    for cmd in _iter_command_classes(module):
        if inproject or not cmd.requires_project:
            cmdname = cmd.__module__.split('.')[-1]
            d[cmdname] = cmd()
    return d


def _get_commands_from_entry_points(inproject, group='devspace.commands'):
    cmds = {}
    for entry_point in pkg_resources.iter_entry_points(group):
        obj = entry_point.load()
        if inspect.isclass(obj):
            cmds[entry_point.name] = obj()
        else:
            raise Exception("Invalid entry point %s" % entry_point.name)
    return cmds


def _get_commands_dict(settings, inproject):
    cmds = _get_commands_from_module('devspace.commands', inproject)
    cmds.update(_get_commands_from_entry_points(inproject))
    cmds_module = settings['COMMANDS_MODULE']
    if cmds_module:
        cmds.update(_get_commands_from_module(cmds_module, inproject))
    return cmds


def _pop_command_name(argv):
    i = 0
    for arg in argv[1:]:
        if not arg.startswith('-'):
            del argv[i]
            return arg
        i += 1


def _print_header(settings, inproject):
    if inproject:
        print("Devspace %s - project: %s\n" % (devspace.__version__, settings['project']))
    else:
        print("Devspace %s - no active project\n" % devspace.__version__)


def _print_commands(settings, inproject):
    _print_header(settings, inproject)
    print("Usage:")
    print("  devspace <command> [options] [args]\n")
    print("Available commands:")
    cmds = _get_commands_dict(settings, inproject)
    for cmdname, cmdclass in sorted(cmds.items()):
        print("  %-13s %s" % (cmdname, cmdclass.short_desc()))
    if not inproject:
        print()
        print("  [ more ]      More commands available when run from project directory")
    print()
    print('Use "devspace <command> -h" to see more info about a command')


def _print_unknown_command(settings, cmdname, inproject):
    _print_header(settings, inproject)
    print("Unknown command: %s\n" % cmdname)
    print('Use "devspace" to see available commands')


def _run_print_help(parser, func, *a, **kw):
    try:
        func(*a, **kw)
    except UsageError as e:
        if str(e):
            parser.error(str(e))
        if e.print_help:
            parser.print_help()
        sys.exit(2)


def _run_command(cmd, args, opts):
    cmd.run(args, opts)


def execute(argv=None, settings=None):
    if argv is None:
        argv = sys.argv

    if settings is None:
        settings = Settings()

    inproject = inside_project()
    if inproject:
        if not get_project_settings(settings):
            sys.exit(2)
    cmds = _get_commands_dict(settings, inproject)
    cmdname = _pop_command_name(argv)
    parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(),
        conflict_handler='resolve')
    if not cmdname:
        _print_commands(settings, inproject)
        sys.exit(0)
    elif cmdname not in cmds:
        _print_unknown_command(settings, cmdname, inproject)
        sys.exit(2)

    cmd = cmds[cmdname]
    parser.usage = "devspace %s %s" % (cmdname, cmd.syntax())
    parser.description = cmd.long_desc()
    cmd.settings = settings
    cmd.add_options(parser)
    opts, args = parser.parse_args(args=argv[1:])
    _run_print_help(parser, cmd.process_options, args, opts)
    _run_print_help(parser, _run_command, cmd, args, opts)
    sys.exit(cmd.exitcode)


if __name__ == '__main__':
    argv_init_project_only = [
        'devspace', 'init', 'test', 'E:/Git/DevSpace/workdir','--extra',
        'author=yang <d12y12@hotmail.com>', '--extra', 'version=0.1.0',
        '--projectonly'
    ]
    argv_init = [
        'devspace', 'init', 'test', 'E:/Git/DevSpace/workdir', '--extra',
        'author=yang <d12y12@hotmail.com>', '--extra', 'version=0.1.0',
    ]
    argv_show = ['devspace', 'show']
    execute(argv_init)
