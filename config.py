import time

from qt.core import QWidget, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit
from calibre.utils.config import JSONConfig
from calibre_plugins.highlights_to_obsidian.send import (title_default_format, body_default_format,
                                                         vault_default_name, no_notes_default_format)

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


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        # header
        self.config_label = QLabel('Highlights to Obsidian Config')
        self.l.addWidget(self.config_label)
        # this linebreak has to be long so that it expands the width of the config window
        self.config_linebreak_label = QLabel("=" * 60)
        self.l.addWidget(self.config_linebreak_label)

        # obsidian vault name
        self.vault_label = QLabel('Obsidian vault name:')
        self.l.addWidget(self.vault_label)

        self.vault_input = QLineEdit(self)
        self.vault_input.setText(prefs['vault_name'])
        self.vault_input.setPlaceholderText("Name of Obsidian vault")
        self.l.addWidget(self.vault_input)
        self.vault_label.setBuddy(self.vault_input)

        # obsidian note title format
        self.title_format_label = QLabel('Obsidian note title format:')
        self.l.addWidget(self.title_format_label)

        self.title_format_input = QLineEdit(self)
        self.title_format_input.setText(prefs['title_format'])
        self.title_format_input.setPlaceholderText("Obsidian note title format")
        self.l.addWidget(self.title_format_input)
        self.title_format_label.setBuddy(self.title_format_input)

        # obsidian note body format
        self.body_format_label = QLabel('Obsidian note body format:')
        self.l.addWidget(self.body_format_label)

        self.body_format_input = QPlainTextEdit(self)
        self.body_format_input.setPlainText(prefs['body_format'])
        self.body_format_input.setPlaceholderText("Obsidian note body format")
        self.l.addWidget(self.body_format_input)
        self.body_format_label.setBuddy(self.body_format_input)

        # obsidian no notes body format
        self.no_notes_format_label = QLabel('Body format for highlights without notes (empty defaults to body format):')
        self.l.addWidget(self.no_notes_format_label)

        self.no_notes_format_input = QPlainTextEdit(self)
        self.no_notes_format_input.setPlainText(prefs['no_notes_format'])
        self.no_notes_format_input.setPlaceholderText("Body format for highlights without notes")
        self.l.addWidget(self.no_notes_format_input)
        self.no_notes_format_label.setBuddy(self.no_notes_format_input)

        # todo: explain note formatting options

        # time setting
        self.time_label = QLabel('Last time highlights were sent:')
        self.l.addWidget(self.time_label)

        self.time_input = QLineEdit(self)
        self.time_input.setText(prefs['last_send_time'])
        self.l.addWidget(self.time_input)
        self.time_label.setBuddy(self.time_input)

        self.time_format_label = QLabel("Time must be formatted: \"YYYY-MM-DD hh:mm:ss\"")
        self.l.addWidget(self.time_format_label)

        # todo: add button to set time to time.localtime()

    def save_settings(self):
        prefs['vault_name'] = self.vault_input.text()
        prefs['title_format'] = self.title_format_input.text()
        prefs['body_format'] = self.body_format_input.toPlainText()
        prefs['no_notes_format'] = self.no_notes_format_input.toPlainText()
        prefs['last_send_time'] = self.time_input.text()
