import re

from plugin import *


class words_blacklist(plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.blacklist = set()

    def on_pubmsg(self, source, msg, **kwargs):
        for word in self.blacklist:
            if re.findall(word, msg) and not self.bot.is_user_op(source.nick):
                if self.am_i_channel_operator():
                    self.bot.kick(source.nick, 'watch your language!')
                    self.logger.info(f'{source.nick} kicked [{word}]')
                else:
                    self.logger.warning(f'{source.nick} cannot be kicked [{word}], operator privileges needed')

    @command(admin=True)
    @doc('ban_word <word>...: ban <word> words. when one of them appears on chat, bot will kick its sender')
    def ban_word(self, sender_nick, args, **kwargs):
        if not args: return
        suffix = ', but I need operator privileges to kick ;(' if not self.am_i_channel_operator() else ''
        self.blacklist.update(args)
        self.bot.say(f'{args} banned{suffix}')
        self.logger.info(f'words {args} banned by {sender_nick}')

    @command(admin=True)
    @doc('unban_word <word>...: unban <word> words')
    def unban_word(self, sender_nick, args, **kwargs):
        to_unban = [arg for arg in args if arg in self.blacklist]
        if not to_unban: return
        for arg in to_unban:
            self.blacklist.remove(arg)

        self.bot.say(f'{to_unban} unbanned')
        self.logger.info(f'words {to_unban} unbanned by {sender_nick}')

    def am_i_channel_operator(self):
        return self.bot.get_channel().is_oper(self.bot.get_nickname())
