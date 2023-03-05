from functools import partial
from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre_plugins.highlights_to_obsidian.button_actions import (help_menu, send_new_highlights,
                                                                   send_all_highlights, resend_highlights,
                                                                   send_new_selected_highlights, send_all_selected_highlights)
from calibre_plugins.highlights_to_obsidian.config import prefs
from calibre_plugins.highlights_to_obsidian.__init__ import version


class MainDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):

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
        self.spacing = 10

        # header
        self.menu_label = QLabel(f'<b>Highlights to Obsidian v{version}</b>', self)
        self.l.addWidget(self.menu_label)

        self.l.addSpacing(self.spacing)

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

        # send new highlights of selected books button
        self.send_new_selected_button = QPushButton("Send new highlights of selected books", self)
        self.send_new_selected_button.clicked.connect(partial(send_new_selected_highlights, self, db))
        self.l.addWidget(self.send_new_selected_button)

        # send all highlights of selected books button
        self.send_all_selected_button = QPushButton("Send all highlights of selected books", self)
        self.send_all_selected_button.clicked.connect(partial(send_all_selected_highlights, self, db))
        self.l.addWidget(self.send_all_selected_button)

        # separate function buttons from config and help
        self.l.addSpacing(self.spacing)

        # button to open config
        self.conf_button = QPushButton(
            'Configure this plugin', self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        # help menu button
        self.help_button = QPushButton("Help", self)
        self.help_button.clicked.connect(partial(help_menu, self))
        self.l.addWidget(self.help_button)

        self.resize(self.sizeHint())

        if prefs["display_help_on_menu_open"]:
            help_menu(self)
            prefs["display_help_on_menu_open"] = False


    def config(self):
        self.do_user_config(parent=self)
        # if any config changes require updating self, do it here
