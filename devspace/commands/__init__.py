"""
Base class for DevSpace commands
"""

from optparse import OptionGroup


class DevSpaceCommand(object):

    requires_project = False
    crawler_process = None
    exitcode = 0

    def __init__(self):
        self.settings = None  # set in devspace.cmdline

    def syntax(self):
        """
        Command syntax (preferably one-line). Do not include command name.
        """
        return ""

    def short_desc(self):
        """
        A short description of the command
        """
        return ""

    def long_desc(self):
        """A long description of the command. Return short description when not
        available. It cannot contain newlines, since contents will be formatted
        by optparser which removes newlines and wraps text.
        """
        return self.short_desc()

    def help(self):
        """An extensive help for the command. It will be shown when using the
        "help" command. It can contain newlines, since not post-formatting will
        be applied to its contents.
        """
        return self.long_desc()

    def add_options(self, parser):
        """
        Populate option parse with options available for this command
        """
        group = OptionGroup(parser, "Global Options")
        group.add_option("--logfile", metavar="FILE",
                         help="log file. if omitted stderr will be used")
        group.add_option("-L", "--loglevel", metavar="LEVEL", default=None,
                         help="log level (default: %s)" % self.settings['LOG_LEVEL'])
        group.add_option("--nolog", action="store_true",
                         help="disable logging completely")

        parser.add_option_group(group)

    def process_options(self, args, opts):
        if opts.logfile:
            self.settings.set('LOG_ENABLED', True)
            self.settings.set('LOG_FILE', opts.logfile)

        if opts.loglevel:
            self.settings.set('LOG_ENABLED', True)
            self.settings.set('LOG_LEVEL', opts.loglevel)

        if opts.nolog:
            self.settings.set('LOG_ENABLED', False)

    def run(self, args, opts):
        """
        Entry point for running commands
        """
        raise NotImplementedError