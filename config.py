import time

from qt.core import QWidget, QVBoxLayout, QLabel, QLineEdit
from calibre.utils.config import JSONConfig
from calibre_plugins.highlights_to_obsidian.send import title_default_format, body_default_format, vault_default_name

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
# todo: keep track of uuids of highlights that have been sent
# this can be done retroactively by saving the uuids of all highlights
# that were made before last_send_time


class ConfigWidget(QWidget):

    def __init__(self):

        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        # obsidian vault name
        self.vault_label = QLabel('Obsidian vault name:')
        self.l.addWidget(self.vault_label)

        self.vault_msg = QLineEdit(self)
        self.vault_msg.setText(prefs['vault_name'])
        self.l.addWidget(self.vault_msg)
        self.vault_label.setBuddy(self.vault_msg)

        # obsidian note title format
        self.title_format_label = QLabel('Obsidian note title format:')
        self.l.addWidget(self.title_format_label)

        self.title_format_msg = QLineEdit(self)
        self.title_format_msg.setText(prefs['title_format'])
        self.l.addWidget(self.title_format_msg)
        self.title_format_label.setBuddy(self.title_format_msg)

        # obsidian note body format
        self.body_format_label = QLabel('Obsidian vault name:')
        self.l.addWidget(self.body_format_label)

        self.body_format_msg = QLineEdit(self)
        self.body_format_msg.setText(prefs['body_format'])
        self.l.addWidget(self.body_format_msg)
        self.body_format_label.setBuddy(self.body_format_msg)

        # todo: explain note formatting options

        # time setting
        self.time_label = QLabel('Last time highlights were sent:')
        self.l.addWidget(self.time_label)

        self.time_msg = QLineEdit(self)
        self.time_msg.setText(prefs['last_send_time'])
        self.l.addWidget(self.time_msg)
        self.time_label.setBuddy(self.time_msg)

        self.time_format_label = QLabel("Time must be formatted: \"YYYY-MM-DD hh:mm:ss\"")
        self.l.addWidget(self.time_format_label)

        # todo: add button to set time to now

    def save_settings(self):
        prefs['vault_name'] = self.vault_msg.text()
        prefs['title_format'] = self.title_format_msg.text()
        prefs['body_format'] = self.body_format_msg.text()
