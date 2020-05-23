"""
Exceptions
"""


# Commands
class UsageError(Exception):
    """To indicate a command-line usage error"""

    def __init__(self, *a, **kw):
        self.print_help = kw.pop('print_help', True)
        super(UsageError, self).__init__(*a, **kw)


# Settings
class ConfigurationError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
