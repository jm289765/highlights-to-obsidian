import time

from qt.core import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                     QPushButton, QDialog, QDialogButtonBox, QCheckBox)
from calibre.gui2 import warning_dialog
from calibre.utils.config import JSONConfig
from calibre_plugins.highlights_to_obsidian.highlight_sender import (title_default_format, body_default_format,
                                                                     vault_default_name, no_notes_default_format,
                                                                     header_default_format, sort_key_default)

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/highlights_to_obsidian) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/highlights_to_obsidian')

# Set defaults
# set time to 2 days after unix epoch start. hopefully prevents platform-dependent invalid default
# last_send_time when using time.mktime()
prefs.defaults['last_send_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(172800))
prefs.defaults['vault_name'] = vault_default_name
prefs.defaults['title_format'] = title_default_format
prefs.defaults['body_format'] = body_default_format
prefs.defaults['no_notes_format'] = no_notes_default_format
prefs.defaults['header_format'] = header_default_format
prefs.defaults['use_header'] = ""  # empty string is equal to false
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

        self.formatting_dialog = FormattingDialog()
        self.format_config_button = QPushButton("Formatting Options")
        self.format_config_button.clicked.connect(self.formatting_dialog.exec)
        self.l.addWidget(self.format_config_button)

        self.other_dialog = OtherConfigDialog()
        self.other_config_button = QPushButton("Other Options")
        self.other_config_button.clicked.connect(self.other_dialog.exec)
        self.l.addWidget(self.other_config_button)

    def save_settings(self):
        # saving is handled in the config dialog classes
        pass


class FormattingDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 80
        self.spacing = 20  # pixels

        self.title_label = QLabel("Formatting Options")
        self.l.addWidget(self.title_label)
        self.title_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.title_linebreak)

        # note formatting info
        format_info = "The title and body have the following formatting options. " + \
                      "To use one, put it in curly brackets, as in {title} or {blockquote}."
        self.note_format_label = QLabel(format_info, self)
        self.l.addWidget(self.note_format_label)

        self.note_format_list_labels = []
        self.make_format_info_labels()

        self.info_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.info_linebreak)

        self.l.addSpacing(self.spacing)

        # obsidian note title format
        self.title_format_label = QLabel('Note title format:', self)
        self.l.addWidget(self.title_format_label)

        self.title_format_input = QLineEdit(self)
        self.title_format_input.setText(prefs['title_format'])
        self.title_format_input.setPlaceholderText("Note title format...")
        self.l.addWidget(self.title_format_input)
        self.title_format_label.setBuddy(self.title_format_input)

        self.l.addSpacing(self.spacing)

        # obsidian note body format
        self.body_format_label = QLabel('Note body format:', self)
        self.l.addWidget(self.body_format_label)

        self.body_format_input = QPlainTextEdit(self)
        self.body_format_input.setPlainText(prefs['body_format'])
        self.body_format_input.setPlaceholderText("Note body format...")
        self.l.addWidget(self.body_format_input)
        self.body_format_label.setBuddy(self.body_format_input)

        self.l.addSpacing(self.spacing)

        # obsidian no notes body format
        self.no_notes_format_label = QLabel('Body format for highlights without notes (if empty, defaults to the above):',
                                            self)
        self.l.addWidget(self.no_notes_format_label)

        self.no_notes_format_input = QPlainTextEdit(self)
        self.no_notes_format_input.setPlainText(prefs['no_notes_format'])
        self.no_notes_format_input.setPlaceholderText("Body format for highlights without notes...")
        self.l.addWidget(self.no_notes_format_input)
        self.no_notes_format_label.setBuddy(self.no_notes_format_input)

        self.l.addSpacing(self.spacing)

        # label for header formatting options
        self.header_format_label = QLabel('Header format (cannot use highlight-specific formatting options):', self)
        self.l.addWidget(self.header_format_label)

        # checkbox to disable or enable using header
        self.header_checkbox = QCheckBox("Use header when sending highlights")
        if prefs['use_header']:
            self.header_checkbox.setChecked(True)
        self.l.addWidget(self.header_checkbox)

        # text box for header formatting options
        self.header_format_input = QPlainTextEdit(self)
        self.header_format_input.setPlainText(prefs['header_format'])
        self.header_format_input.setPlaceholderText("Header format...")
        self.l.addWidget(self.header_format_input)
        self.header_format_label.setBuddy(self.header_format_input)

        self.l.addSpacing(self.spacing)

        # ok and cancel buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.ok_button)
        self.buttons.rejected.connect(self.cancel_button)
        self.l.addWidget(self.buttons)

    def make_format_info_labels(self):

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

        time_note = QLabel("Note that times are the time the highlight was made, not the current time.")
        self.l.addWidget(time_note)

    def save_settings(self):
        prefs['title_format'] = self.title_format_input.text()
        prefs['body_format'] = self.body_format_input.toPlainText()
        prefs['no_notes_format'] = self.no_notes_format_input.toPlainText()
        prefs['header_format'] = self.header_format_input.toPlainText()
        prefs['use_header'] = "True" if self.header_checkbox.isChecked() else ""  # empty string is equal to false

    def ok_button(self):
        self.save_settings()
        self.done(QDialog.Accepted)

    def cancel_button(self):
        self.done(QDialog.Rejected)


class OtherConfigDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 80
        self.spacing = 20  # pixels

        self.setWindowTitle("Highlights to Obsidian: Other Configuration Options")

        self.title_label = QLabel("Other configuration options")
        self.l.addWidget(self.title_label)
        self.title_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.title_linebreak)

        self.l.addSpacing(self.spacing)

        # obsidian vault name
        self.vault_label = QLabel('Obsidian vault name:', self)
        self.l.addWidget(self.vault_label)

        self.vault_input = QLineEdit(self)
        self.vault_input.setText(prefs['vault_name'])
        self.vault_input.setPlaceholderText("Obsidian vault name...")
        self.l.addWidget(self.vault_input)
        self.vault_label.setBuddy(self.vault_input)

        self.l.addSpacing(self.spacing)

        # sort key
        self.sort_label = QLabel("Sort key: used to sort highlights that get sent to the same file. "
                                 + "(Sort key can be any of the formatting option. No brackets. "
                                 + "For example, timestamp or location.)", self)
        self.l.addWidget(self.sort_label)

        self.sort_input = QLineEdit(self)
        self.sort_input.setText(prefs['sort_key'])
        self.l.addWidget(self.sort_input)
        self.sort_label.setBuddy(self.sort_input)

        self.l.addSpacing(self.spacing)

        # time setting
        self.time_label = QLabel('Last time highlights were sent (highlights made after this are considered new)', self)
        self.l.addWidget(self.time_label)

        # time format info
        self.time_format_label = QLabel("Time must be formatted: \"YYYY-MM-DD hh:mm:ss\"")
        self.l.addWidget(self.time_format_label)

        self.time_input = QLineEdit(self)
        self.time_input.setText(prefs['last_send_time'])
        self.l.addWidget(self.time_input)
        self.time_label.setBuddy(self.time_input)

        # button to set time to now
        self.set_time_now_button = QPushButton("Set last send time to now (UTC)", self)
        self.set_time_now_button.clicked.connect(self.set_time_now)
        self.l.addWidget(self.set_time_now_button)

        self.l.addSpacing(self.spacing)

        # ok and cancel buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.ok_button)
        self.buttons.rejected.connect(self.cancel_button)
        self.l.addWidget(self.buttons)

    def set_time_now(self):
        prefs["last_send_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        self.time_input.setText(prefs['last_send_time'])

    def save_settings(self):
        prefs['vault_name'] = self.vault_input.text()
        prefs['sort_key'] = self.sort_input.text()

        # validate time input
        send_time = self.time_input.text()
        try:
            # todo: move all the scattered calls to mktime(strptime()) to a single place, so i don't have to keep
            #  copying and pasting the format
            time.mktime(time.strptime(send_time, "%Y-%m-%d %H:%M:%S"))
            prefs['last_send_time'] = send_time
        except:
            txt = f'Could not parse time "{send_time}". Either it is formatted improperly or the year is too high' + \
                  f' or low.\n\n Keeping previous time "{prefs["last_send_time"]}" instead.'
            warning_dialog(self, "Invalid Time", txt, show=True)

    def ok_button(self):
        self.save_settings()
        self.done(QDialog.Accepted)

    def cancel_button(self):
        self.done(QDialog.Rejected)
