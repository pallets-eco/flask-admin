import logging
import shlex
import warnings

from flask import request
from flask.json import jsonify

from jinja2 import Markup

from flask.ext.admin.base import BaseView, expose
from flask.ext.admin.babel import gettext
from flask.ext.admin._compat import VER


class RedisCli(BaseView):
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

        if self.shlex_check and VER < (2, 7, 3):
            warnings.warn('Warning: rediscli uses shlex library and it does not work with unicode until Python 2.7.3. ' +
                          'To remove this warning, upgrade to Python 2.7.3 or suppress it by setting shlex_check attribute ' +
                          'to False.')

    def _inspect_commands(self):
        for name in dir(self.redis):
            if not name.startswith('_'):
                attr = getattr(self.redis, name)
                if callable(attr):
                    doc = (getattr(attr, '__doc__', '') or '').strip()
                    self.commands[name] = (attr, doc)

    def _execute_command(self, name, args):
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
        if VER < (2, 7, 3):
            # shlex can't work with unicode until 2.7.3
            return tuple(x.decode('utf-8') for x in shlex.split(cmd.encode('utf-8')))

        return tuple(shlex.split(cmd))

    def _error(self, msg):
        return Markup('<div class="error">%s</div>' % msg)

    def _result(self, result):
        return self.render('admin/rediscli/response.html',
                           type_name=lambda d: type(d).__name__,
                           result=result)

    @expose('/')
    def console_view(self):
        return self.render('admin/rediscli/console.html')

    @expose('/run/', methods=('POST',))
    def execute_view(self):
        try:
            cmd = request.form.get('cmd').lower()
            if not cmd:
                return self._error('Cli: Empty command.')

            parts = self._parse_cmd(cmd)
            if not parts:
                return self._error('Cli: Failed to parse command.')

            return self._execute_command(parts[0], parts[1:])
        except Exception as ex:
            logging.exception(ex)
            return self._error('Cli: %s' % ex)
