import time

from qt.core import QWidget, QHBoxLayout, QLabel, QLineEdit
from calibre.utils.config import JSONConfig

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/highlights_to_obsidian) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/highlights_to_obsidian')

# Set defaults
prefs.defaults['hello_world_msg'] = 'Hello, World!'
prefs.defaults['last_send_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QHBoxLayout()
        self.setLayout(self.l)

        self.label = QLabel('Hello world &message:')
        self.l.addWidget(self.label)

        self.msg = QLineEdit(self)
        self.msg.setText(prefs['hello_world_msg'])
        self.l.addWidget(self.msg)
        self.label.setBuddy(self.msg)

        # time format: "%Y-%m-%d %H:%M:%S"

    def save_settings(self):
        prefs['hello_world_msg'] = self.msg.text()
