import logging
import shlex
import warnings

from flask import request

from jinja2 import Markup

from flask_admin.base import BaseView, expose
from flask_admin.babel import gettext
from flask_admin._compat import VER

# Set up logger
log = logging.getLogger("flask-admin.redis")


class CommandError(Exception):
    """
        RedisCli error exception.
    """
    pass


class TextWrapper(str):
    """
        Small text wrapper for result formatter to distinguish between
        different string types.
    """
    pass


class RedisCli(BaseView):
    """
        Simple redis console.

        To use it, simply pass `Redis` connection object to the constructor.
    """

    shlex_check = True
    """
        shlex from stdlib does not work with unicode on 2.7.2 and lower.
        If you want to suppress warning, set this attribute to False.
    """

    remapped_commands = {
        'del': 'delete'
    }
    """
        List of redis remapped commands.
    """

    excluded_commands = set(('pubsub', 'set_response_callback', 'from_url'))
    """
        List of excluded commands.
    """

    def __init__(self, redis,
                 name=None, category=None, endpoint=None, url=None):
        """
            Constructor.

            :param redis:
                Redis connection
            :param name:
                View name. If not provided, will use the model class name
            :param category:
                View category
            :param endpoint:
                Base endpoint. If not provided, will use the model name + 'view'.
                For example if model name was 'User', endpoint will be
                'userview'
            :param url:
                Base URL. If not provided, will use endpoint as a URL.
        """
        super(RedisCli, self).__init__(name, category, endpoint, url)

        self.redis = redis

        self.commands = {}

        self._inspect_commands()
        self._contribute_commands()

        if self.shlex_check and VER < (2, 7, 3):
            warnings.warn('Warning: rediscli uses shlex library and it does '
                          'not work with unicode until Python 2.7.3. To '
                          'remove this warning, upgrade to Python 2.7.3 or '
                          'suppress it by setting shlex_check attribute '
                          'to False.')

    def _inspect_commands(self):
        """
            Inspect connection object and extract command names.
        """
        for name in dir(self.redis):
            if not name.startswith('_'):
                attr = getattr(self.redis, name)
                if callable(attr) and name not in self.excluded_commands:
                    doc = (getattr(attr, '__doc__', '') or '').strip()
                    self.commands[name] = (attr, doc)

        for new, old in self.remapped_commands.items():
            self.commands[new] = self.commands[old]

    def _contribute_commands(self):
        """
            Contribute custom commands.
        """
        self.commands['help'] = (self._cmd_help, 'Help!')

    def _execute_command(self, name, args):
        """
            Execute single command.

            :param name:
                Command name
            :param args:
                Command arguments
        """
        # Do some remapping
        new_cmd = self.remapped_commands.get(name)
        if new_cmd:
            name = new_cmd

        # Execute command
        if name not in self.commands:
            return self._error(gettext('Cli: Invalid command.'))

        handler, _ = self.commands[name]
        return self._result(handler(*args))

    def _parse_cmd(self, cmd):
        """
            Parse command by using shlex module.

            :param cmd:
                Command to parse
        """
        if VER < (2, 7, 3):
            # shlex can't work with unicode until 2.7.3
            return tuple(x.decode('utf-8') for x in shlex.split(cmd.encode('utf-8')))

        return tuple(shlex.split(cmd))

    def _error(self, msg):
        """
            Format error message as HTTP response.

            :param msg:
                Message to format
        """
        return Markup('<div class="error">%s</div>' % msg)

    def _result(self, result):
        """
            Format result message as HTTP response.

            :param msg:
                Result to format.
        """
        return self.render('admin/rediscli/response.html',
                           type_name=lambda d: type(d).__name__,
                           result=result)

    # Commands
    def _cmd_help(self, *args):
        """
            Help command implementation.
        """
        if not args:
            help = 'Usage: help <command>.\nList of supported commands: '
            help += ', '.join(n for n in sorted(self.commands))
            return TextWrapper(help)

        cmd = args[0]
        if cmd not in self.commands:
            raise CommandError('Invalid command.')

        help = self.commands[cmd][1]
        if not help:
            return TextWrapper('Command does not have any help.')

        return TextWrapper(help)

    # Views
    @expose('/')
    def console_view(self):
        """
            Console view.
        """
        return self.render('admin/rediscli/console.html')

    @expose('/run/', methods=('POST',))
    def execute_view(self):
        """
            AJAX API.
        """
        try:
            cmd = request.form.get('cmd')
            if not cmd:
                return self._error('Cli: Empty command.')

            parts = self._parse_cmd(cmd)
            if not parts:
                return self._error('Cli: Failed to parse command.')

            return self._execute_command(parts[0], parts[1:])
        except CommandError as err:
            return self._error('Cli: %s' % err)
        except Exception as ex:
            log.exception(ex)
            return self._error('Cli: %s' % ex)
