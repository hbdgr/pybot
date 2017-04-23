from plugin import *


class irc_privmsg_logger_handler(logging.StreamHandler):
    def __init__(self, connection, plhs):
        self.plhs = plhs
        self.connection = connection
        super().__init__()

    def emit(self, record):
        if record.funcName == 'send_raw': return
        try:
            msg = self.format(record)
            for target, level in self.plhs.items():
                if record.levelno >= level and self.connection.is_connected():
                    self.connection.privmsg(target, msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


class privmsg_logger_handler(plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.logger = logging.getLogger(__name__)
        self.plhs = {}  # username -> logging_level
        self.plh_handler = irc_privmsg_logger_handler(self.bot.connection, self.plhs)
        self.plh_handler.setFormatter(logging.Formatter('%(levelname)-10s%(filename)s:%(funcName)-16s: %(message)s'))
        self.plh_handler.setLevel(logging.DEBUG)
        logging.getLogger('').addHandler(self.plh_handler)

        self.int_to_level_str = {
            logging.CRITICAL: 'critical',
            logging.FATAL: 'fatal',
            logging.ERROR: 'error',
            logging.WARNING: 'warning',
            logging.WARN: 'warn',
            logging.INFO: 'info',
            logging.DEBUG: 'debug',
            logging.NOTSET: 'all',
        }

        self.level_str_to_int = {
            'critical': logging.CRITICAL,
            'fatal': logging.FATAL,
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'warn': logging.WARN,
            'info': logging.INFO,
            'debug': logging.DEBUG,
            'notset': logging.NOTSET,
            'all': logging.NOTSET
        }

    def unload_plugin(self):
        logging.getLogger('').removeHandler(self.plh_handler)

    @command
    @admin
    def add_plh(self, sender_nick, args, **kwargs):
        if not args: return
        level = args[0].strip().lower()
        if level not in self.level_str_to_int: return
        self.logger.warning('plh added: %s at %s' % (sender_nick, level))
        level = self.level_str_to_int[level]
        self.plhs[sender_nick] = level
        self.bot.send_response_to_channel('plh added: %s at %s' % (sender_nick, self.int_to_level_str[level]))

    @command
    @admin
    def rm_plh(self, sender_nick, **kwargs):
        if sender_nick not in self.plhs: return
        del self.plhs[sender_nick]
        self.logger.info('plh for %s removed' % sender_nick)
        self.bot.send_response_to_channel('plh removed')

    @command
    def get_plhs(self, sender_nick, **kwargs):
        response = self.plhs.copy()
        for target, level in response.items():
            response[target] = self.int_to_level_str[level]

        self.bot.send_response_to_channel('privmsg logger handlers registered: %s' % response)
        self.logger.info('plhs given to %s: %s' % (sender_nick, response))