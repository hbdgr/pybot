import os
import sqlite3

from threading import Lock
from fuzzywuzzy import process, fuzz
from plugin import *


class get(plugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.db_name = "get"
        os.makedirs(os.path.dirname(os.path.realpath(self.config['db_location'])), exist_ok=True)
        self.db_connection = sqlite3.connect(self.config['db_location'], check_same_thread=False)
        self.db_cursor = self.db_connection.cursor()
        self.db_cursor.execute(f"CREATE TABLE IF NOT EXISTS '{self.db_name}' (entry TEXT primary key not null, val TEXT)")  # key -> value
        self.db_mutex = Lock()
        self.case_insensitive_text = 'COLLATE NOCASE' if not self.config['case_sensitive'] else ''

    @command
    @doc('get <entry>: get saved message for <entry>')
    def get(self, sender_nick, msg, **kwargs):
        if not msg: return
        entry = self.prepare_entry(msg)
        with self.db_mutex:
            self.db_cursor.execute(f"SELECT val FROM '{self.db_name}' WHERE entry = ? {self.case_insensitive_text}", (entry,))
            result = self.db_cursor.fetchone()

        result = result[0] if result else None
        self.logger.info(f'{sender_nick} gets {entry}: {result}')
        if result: self.bot.say(color.cyan(f'[{entry}] ') + result)
        else:
            response = 'no such entry'
            possible_entry = self.get_best_entry_match(entry) if self.config['try_autocorrect'] else None
            if possible_entry:
                fixed_command = f'get {possible_entry}'
                response = f'{response}, did you mean {possible_entry}?'
                self.bot.register_fixed_command(fixed_command)
            self.bot.say(response)

    @command
    @doc("get all saved messages")
    def get_list(self, sender_nick, **kwargs):
        self.logger.info(f'{sender_nick} gets entry list')
        result = sorted(self.get_list_impl())
        response = f'saved entries: {", ".join(result)}' if result else 'no saved entries'
        self.bot.say(response)

    @command
    @doc("get all saved messages")
    def get_all(self, **kwargs):
        return self.get_list(**kwargs)

    @command(admin=True)
    @doc('unset <entry>: remove <entry> entry')
    def unset(self, sender_nick, msg, **kwargs):
        if not msg: return
        entry = self.prepare_entry(msg)
        with self.db_mutex:
            self.db_cursor.execute(f"DELETE FROM '{self.db_name}' WHERE entry = ? {self.case_insensitive_text}", (entry,))
            self.db_connection.commit()

        self.bot.say_ok()
        self.logger.info(f'{sender_nick} removes {entry}')

    @command(admin=True)
    @doc('set <entry> <message>: save <message> for <entry>')
    def set(self, sender_nick, msg, **kwargs):
        if not msg: return
        entry = msg.split()[0]
        val = msg[len(entry):].strip()
        if not val: return
        entry = self.prepare_entry(entry)

        try:
            with self.db_mutex:
                self.db_cursor.execute(f"INSERT INTO '{self.db_name}' VALUES (?, ?)", (entry, val))
                self.db_connection.commit()

            self.logger.info(f'{sender_nick} sets {entry}: {val}')
            self.bot.say_ok()
        except sqlite3.IntegrityError:
            self.bot.say(f'"{entry}" entry already exists')
            return

    def get_list_impl(self):
        with self.db_mutex:
            self.db_cursor.execute(f"SELECT entry FROM '{self.db_name}'")
            result = self.db_cursor.fetchall()

        return [t[0] for t in result]

    def prepare_entry(self, entry):
        result = entry.split()[0].strip()
        return result

    def get_best_entry_match(self, entry):
        choices = [c.replace('_', ' ') for c in self.get_list_impl()]
        entry = entry.replace('_', ' ')
        result = process.extract(entry, choices, scorer=fuzz.token_sort_ratio)
        result = [(r[0].replace(' ', '_'), r[1]) for r in result]
        return result[0][0] if result[0][1] > 65 else None
