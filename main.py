from functools import partial
from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre_plugins.highlights_to_obsidian.send import send_new_highlights, send_all_highlights, resend_highlights


class MainDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        # todo: if this is the first time the extension has been used, open a popup telling the
        # user to set config and, if they don't want to send all notes, last_send_time. also keyboard
        # shortcut in Preferences -> Shortcuts -> Send Highlights to Obsidian
        # make this popup be a help menu that's also accessible from a button in this dialog window.
        # also add the help, and a config button as actions in menu_button.py
        # shortcuts that are available include ctrl+s, ctrl+e, ctrl+g, ctrl+h, ctrl+j, ctrl+k
        # this can use the info_dialog function used in this class's update_metadata

        QDialog.__init__(self, gui)
        self.gui = gui
        self.do_user_config = do_user_config

        # The current database shown in the GUI
        # db is an instance of the class LibraryDatabase from db/legacy.py
        # This class has many, many methods that allow you to do a lot of
        # things. For most purposes you should use db.new_api, which has
        # a much nicer interface from db/cache.py
        self.db = gui.current_db
        db = self.db.new_api

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        # button to open config
        self.conf_button = QPushButton(
            'Configure this plugin', self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        # send new highlights button
        self.send_button = QPushButton("Send new highlights to obsidian", self)
        self.send_button.clicked.connect(partial(send_new_highlights, self, db))
        self.l.addWidget(self.send_button)

        # send all highlights button
        self.send_all_button = QPushButton("Send all highlights to obsidian", self)
        self.send_all_button.clicked.connect(partial(send_all_highlights, self, db))
        self.l.addWidget(self.send_all_button)

        # resend previously sent highlights button
        self.resend_button = QPushButton("Resend previously sent highlights", self)
        self.resend_button.clicked.connect(partial(resend_highlights, self, db))
        self.l.addWidget(self.resend_button)

        self.resize(self.sizeHint())

    def config(self):
        self.do_user_config(parent=self)
        # if any config changes require updating self, do it here
