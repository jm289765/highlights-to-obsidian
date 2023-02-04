import time

from qt.core import QWidget, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton
from calibre.utils.config import JSONConfig
from calibre_plugins.highlights_to_obsidian.highlight_sender import (title_default_format, body_default_format,
                                                                     vault_default_name, no_notes_default_format,
                                                                     sort_key_default)

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/highlights_to_obsidian) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/highlights_to_obsidian')

# Set defaults
prefs.defaults['last_send_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(0))
prefs.defaults['vault_name'] = vault_default_name
prefs.defaults['title_format'] = title_default_format
prefs.defaults['body_format'] = body_default_format
prefs.defaults['no_notes_format'] = no_notes_default_format
prefs.defaults['prev_send'] = None  # the send time before last_send_time
prefs.defaults['display_help_on_menu_open'] = True
prefs.defaults['sort_key'] = sort_key_default


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 80

        # header
        self.config_label = QLabel('Highlights to Obsidian Config', self)
        self.l.addWidget(self.config_label)
        # this linebreak has to be long so that it expands the width of the config window
        self.config_linebreak_label = QLabel(self.linebreak, self)
        self.l.addWidget(self.config_linebreak_label)

        # obsidian vault name
        self.vault_label = QLabel('Obsidian vault name:', self)
        self.l.addWidget(self.vault_label)

        self.vault_input = QLineEdit(self)
        self.vault_input.setText(prefs['vault_name'])
        self.vault_input.setPlaceholderText("Name of Obsidian vault")
        self.l.addWidget(self.vault_input)
        self.vault_label.setBuddy(self.vault_input)

        # obsidian note title format
        self.title_format_label = QLabel('Obsidian note title format:', self)
        self.l.addWidget(self.title_format_label)

        self.title_format_input = QLineEdit(self)
        self.title_format_input.setText(prefs['title_format'])
        self.title_format_input.setPlaceholderText("Obsidian note title format")
        self.l.addWidget(self.title_format_input)
        self.title_format_label.setBuddy(self.title_format_input)

        # obsidian note body format
        self.body_format_label = QLabel('Obsidian note body format:', self)
        self.l.addWidget(self.body_format_label)

        self.body_format_input = QPlainTextEdit(self)
        self.body_format_input.setPlainText(prefs['body_format'])
        self.body_format_input.setPlaceholderText("Obsidian note body format")
        self.l.addWidget(self.body_format_input)
        self.body_format_label.setBuddy(self.body_format_input)

        # obsidian no notes body format
        self.no_notes_format_label = QLabel('Body format for highlights without notes (empty defaults to the above):',
                                            self)
        self.l.addWidget(self.no_notes_format_label)

        self.no_notes_format_input = QPlainTextEdit(self)
        self.no_notes_format_input.setPlainText(prefs['no_notes_format'])
        self.no_notes_format_input.setPlaceholderText("Body format for highlights without notes")
        self.l.addWidget(self.no_notes_format_input)
        self.no_notes_format_label.setBuddy(self.no_notes_format_input)

        # note formatting info
        self.note_format_label = None
        self.note_format_list_labels = []
        self.make_format_info_labels()

        # extra line break before time config
        self.time_linebreak_label = QLabel(self.linebreak, self)
        self.l.addWidget(self.time_linebreak_label)

        # sort key
        self.sort_label = QLabel("Sort key: used to sort highlights that get sent to the same file. "
                                 + "(Sort key can be any of the formatting option. No brackets. "
                                 + "For example, timestamp or location.)", self)
        self.l.addWidget(self.sort_label)

        self.sort_input = QLineEdit(self)
        self.sort_input.setText(prefs['sort_key'])
        self.l.addWidget(self.sort_input)
        self.sort_label.setBuddy(self.sort_input)
        # 'Recommended: "timestamp" or "location"'

        # time setting
        self.time_label = QLabel('Last time highlights were sent (highlights made after this are considered new):', self)
        self.l.addWidget(self.time_label)

        self.time_input = QLineEdit(self)
        self.time_input.setText(prefs['last_send_time'])
        self.l.addWidget(self.time_input)
        self.time_label.setBuddy(self.time_input)

        # button to set time to now
        self.set_time_now_button = QPushButton("Set last send time to now (UTC)", self)
        self.set_time_now_button.clicked.connect(self.set_time_now)
        self.l.addWidget(self.set_time_now_button)

        # time format info
        self.time_format_label = QLabel("Time must be formatted: \"YYYY-MM-DD hh:mm:ss\"")
        self.l.addWidget(self.time_format_label)

    def make_format_info_labels(self):
        format_info = "Notes sent to obsidian have the following formatting options. " + \
                      "To use one, put it in curly brackets, as in {title} or {blockquote}."
        self.note_format_label = QLabel(format_info, self)
        self.l.addWidget(self.note_format_label)

        # list of formatting options
        format_options = [
            "title", "authors",
            "highlight", "blockquote",
            "notes", "date",
            "localdate", "time",
            "localtime", "datetime",
            "localdatetime", "day",
            "localday", "month",
            "localmonth", "year",
            "localyear", "timezone",
            "utcoffset", "url",
            "location", "timestamp",
            "bookid", "uuid",
        ]
        f_opt_str = '"' + '", "'.join(format_options) + '"'

        strs = []
        char_count = 0
        start_idx = 0
        for idx in range(len(f_opt_str)):
            char_count += 1
            if char_count > 100 and f_opt_str[idx] == " ":
                strs.append(f_opt_str[start_idx:idx])
                start_idx = idx
                char_count = 0
        strs.append(f_opt_str[start_idx:])

        for s in strs:
            label = QLabel(s, self)
            self.note_format_list_labels.append(label)
            self.l.addWidget(label)

    def save_settings(self):
        prefs['vault_name'] = self.vault_input.text()
        prefs['title_format'] = self.title_format_input.text()
        prefs['body_format'] = self.body_format_input.toPlainText()
        prefs['no_notes_format'] = self.no_notes_format_input.toPlainText()
        prefs['sort_key'] = self.sort_input.text()
        prefs['last_send_time'] = self.time_input.text()

    def set_time_now(self):
        prefs["last_send_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.time_input.setText(prefs['last_send_time'])