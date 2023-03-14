import time

from qt.core import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                     QPushButton, QDialog, QDialogButtonBox, QCheckBox)
from calibre.gui2 import warning_dialog
from calibre.utils.config import JSONConfig
from calibre_plugins.highlights_to_obsidian.highlight_sender import (title_default_format, body_default_format,
                                                                     vault_default_name, no_notes_default_format,
                                                                     header_default_format, sort_key_default)
from calibre_plugins.highlights_to_obsidian.__init__ import version

# This is where all preferences for this plugin will be stored
# Remember that this name (i.e. plugins/highlights_to_obsidian) is also
# in a global namespace, so make it as unique as possible.
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/highlights_to_obsidian')

# Set defaults
# set time to 2 days after unix epoch start. hopefully prevents platform-dependent invalid default
# last_send_time when using time.mktime()

prefs.defaults['vault_name'] = vault_default_name
prefs.defaults['title_format'] = title_default_format
prefs.defaults['body_format'] = body_default_format
prefs.defaults['no_notes_format'] = no_notes_default_format
prefs.defaults['header_format'] = header_default_format
prefs.defaults['use_header'] = False  # empty string is equal to false
prefs.defaults['sort_key'] = sort_key_default

prefs.defaults['last_send_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(172800))
prefs.defaults['prev_send'] = None  # the send time before last_send_time
prefs.defaults['display_help_on_menu_open'] = True
prefs.defaults['confirm_send_all'] = True  # confirmation dialog when sending all highlights
prefs.defaults['highlights_sent_dialog'] = True  # show popup with how many highlights were sent
prefs.defaults['max_note_size'] = "20000"
prefs.defaults['use_max_note_size'] = True  # make max_note_size easy to toggle
prefs.defaults['copy_header'] = False  # whether to copy header when splitting a too-big note
prefs.defaults['web_user'] = False  # whether we should send web user or local user's highlights


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 80
        self.spacing = 10

        # header
        self.config_label = QLabel(f'<b>Highlights to Obsidian v{version}</b>', self)
        self.l.addWidget(self.config_label)

        self.l.addSpacing(self.spacing)

        format_config_button = QPushButton("Formatting Options")
        format_config_button.clicked.connect(self.do_format_config)
        self.l.addWidget(format_config_button)

        self.l.addSpacing(self.spacing)

        other_config_button = QPushButton("Other Options")
        other_config_button.clicked.connect(self.do_other_config)
        self.l.addWidget(other_config_button)

        self.l.addSpacing(self.spacing)

    def do_format_config(self):
        dialog = FormattingDialog()
        dialog.exec()

    def do_other_config(self):
        dialog = OtherConfigDialog()
        dialog.exec()

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

        self.title_label = QLabel("<b>Highlights to Obsidian Formatting Options</b>")
        self.l.addWidget(self.title_label)
        self.title_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.title_linebreak)

        # note formatting info
        format_info = "<b>The following formatting options are available.</b> " + \
                      "To use one, put it in curly brackets, as in {title} or {blockquote}."
        self.note_format_label = QLabel(format_info, self)
        self.l.addWidget(self.note_format_label)

        self.note_format_list_label = None
        self.make_format_info_label()

        self.info_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.info_linebreak)

        self.l.addSpacing(self.spacing)

        # obsidian note title format
        self.title_format_label = QLabel('<b>Note title format:</b>', self)
        self.l.addWidget(self.title_format_label)

        self.title_format_input = QLineEdit(self)
        self.title_format_input.setText(prefs['title_format'])
        self.title_format_input.setPlaceholderText("Note title format...")
        self.l.addWidget(self.title_format_input)
        self.title_format_label.setBuddy(self.title_format_input)

        self.l.addSpacing(self.spacing)

        # obsidian note body format
        self.body_format_label = QLabel('<b>Note body format:</b>', self)
        self.l.addWidget(self.body_format_label)

        self.body_format_input = QPlainTextEdit(self)
        self.body_format_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.body_format_input.setPlainText(prefs['body_format'])
        self.body_format_input.setPlaceholderText("Note body format...")
        self.l.addWidget(self.body_format_input)
        self.body_format_label.setBuddy(self.body_format_input)

        self.l.addSpacing(self.spacing)

        # obsidian no notes body format
        self.no_notes_format_label = QLabel('<b>Body format for highlights without notes</b> (if empty, defaults to the above):',
                                            self)
        self.l.addWidget(self.no_notes_format_label)

        self.no_notes_format_input = QPlainTextEdit(self)
        self.no_notes_format_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.no_notes_format_input.setPlainText(prefs['no_notes_format'])
        self.no_notes_format_input.setPlaceholderText("Body format for highlights without notes...")
        self.l.addWidget(self.no_notes_format_input)
        self.no_notes_format_label.setBuddy(self.no_notes_format_input)

        self.l.addSpacing(self.spacing)

        # label for header formatting options
        self.header_format_label = QLabel('<b>Header format</b> (avoid highlight-specific data like {highlight} or {url}):', self)
        self.l.addWidget(self.header_format_label)

        # text box for header formatting options
        self.header_format_input = QPlainTextEdit(self)
        self.header_format_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.header_format_input.setPlainText(prefs['header_format'])
        self.header_format_input.setPlaceholderText("Header format...")
        self.l.addWidget(self.header_format_input)
        self.header_format_label.setBuddy(self.header_format_input)

        # checkbox to disable or enable using header
        self.header_checkbox = QCheckBox("Use header when sending highlights")
        if prefs['use_header']:
            self.header_checkbox.setChecked(True)
        self.l.addWidget(self.header_checkbox)

        self.l.addSpacing(self.spacing)

        # ok and cancel buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.ok_button)
        self.buttons.rejected.connect(self.cancel_button)
        self.l.addWidget(self.buttons)

    def make_format_info_label(self):

        # list of formatting options
        format_options = [
            "title", "authors",
            "highlight", "blockquote", "notes",
            "date", "time", "datetime",
            "day", "month", "year",
            "hour", "minute", "second",
            "utcnow", "datenow", "timenow",
            "timezone", "utcoffset",
            "url", "location", "timestamp",
            "totalsent", "booksent", "highlightsent",
            "bookid", "uuid",
        ]
        f_opt_str = "'" + "', '".join(format_options) + "'"

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

        one_str = "<br/>".join(strs)
        self.note_format_list_label = QLabel(one_str, self)
        self.l.addWidget(self.note_format_list_label)

        local_note = QLabel("All times use UTC by default. To use local time instead, add 'local' " +
                            "to the beginning: {localdatetime}, {localnow}, etc.")
        self.l.addWidget(local_note)

        time_note = QLabel("Note that all times, except 'now' times, are the time the highlight was made, not the " +
                           "current time.")
        self.l.addWidget(time_note)

    def save_settings(self):
        prefs['title_format'] = self.title_format_input.text()
        prefs['body_format'] = self.body_format_input.toPlainText()
        prefs['no_notes_format'] = self.no_notes_format_input.toPlainText()
        prefs['header_format'] = self.header_format_input.toPlainText()
        prefs['use_header'] = self.header_checkbox.isChecked()

    def ok_button(self):
        self.save_settings()
        self.accept()

    def cancel_button(self):
        self.reject()


class OtherConfigDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        self.linebreak = "=" * 50
        self.spacing = 20  # pixels

        self.setWindowTitle("Highlights to Obsidian: Other Configuration Options")

        self.title_label = QLabel("<b>Highlights to Obsidian Other Options</b>")
        self.l.addWidget(self.title_label)
        self.title_linebreak = QLabel(self.linebreak)
        self.l.addWidget(self.title_linebreak)

        self.l.addSpacing(self.spacing)

        # obsidian vault name
        self.vault_label = QLabel('<b>Obsidian vault name:</b>', self)
        self.l.addWidget(self.vault_label)

        self.vault_input = QLineEdit(self)
        self.vault_input.setText(prefs['vault_name'])
        self.vault_input.setPlaceholderText("Obsidian vault name...")
        self.l.addWidget(self.vault_input)
        self.vault_label.setBuddy(self.vault_input)

        self.l.addSpacing(self.spacing)

        # sort key
        self.sort_label = QLabel("<b>Sort key:</b> used to sort highlights that get sent to the same file.<br/>"
                                 + "(Sort keys can be any of H2O's formatting options. No brackets. "
                                 + "For example, <br/>timestamp or location.)", self)
        self.l.addWidget(self.sort_label)

        self.sort_input = QLineEdit(self)
        self.sort_input.setText(prefs['sort_key'])
        self.l.addWidget(self.sort_input)
        self.sort_label.setBuddy(self.sort_input)

        self.l.addSpacing(self.spacing)

        # time setting
        self.time_label = QLabel('<b>Last time highlights were sent</b> (highlights made after this are considered new)', self)
        self.l.addWidget(self.time_label)

        # time format info
        self.time_format_label = QLabel("Time must be formatted \"YYYY-MM-DD hh:mm:ss\"")
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

        # max note size and related settings
        self.max_size_label = QLabel("<b>Maximum note size</b> (errors can happen when notes are too long):")
        self.l.addWidget(self.max_size_label)

        self.max_size_input = QLineEdit()
        self.max_size_input.setText(prefs['max_note_size'])
        self.max_size_input.setPlaceholderText("Max note size...")
        self.l.addWidget(self.max_size_input)

        self.use_max_size_checkbox = QCheckBox("Restrict length of sent notes to the max note size")
        self.use_max_size_checkbox.setChecked(prefs['use_max_note_size'])
        self.l.addWidget(self.use_max_size_checkbox)

        self.copy_header_checkbox = QCheckBox("When splitting up a long note, include the header in each smaller note")
        self.copy_header_checkbox.setChecked(prefs['copy_header'])
        self.l.addWidget(self.copy_header_checkbox)

        self.l.addSpacing(self.spacing)

        # checkbox for confirmation dialog
        self.show_confirmation_checkbox = QCheckBox("Confirmation dialog when sending all highlights")
        self.show_confirmation_checkbox.setChecked(prefs['confirm_send_all'])
        self.l.addWidget(self.show_confirmation_checkbox)

        # checkbox for showing how many highlights were sent
        self.show_count_checkbox = QCheckBox("After sending highlights, show how many were sent")
        self.show_count_checkbox.setChecked(prefs['highlights_sent_dialog'])
        self.l.addWidget(self.show_count_checkbox)

        self.l.addSpacing(self.spacing)

        # checkbox for local user or web user
        self.web_user_checkbox = QCheckBox("Send web user's highlights (instead of local user's highlights)")
        self.web_user_checkbox.setChecked(prefs['web_user'])
        self.l.addWidget(self.web_user_checkbox)

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
        max_size = self.max_size_input.text()
        prefs['max_note_size'] = max_size if max_size.isnumeric() else prefs['max_note_size']
        prefs['use_max_note_size'] = self.use_max_size_checkbox.isChecked()
        prefs['copy_header'] = self.copy_header_checkbox.isChecked()
        prefs['confirm_send_all'] = self.show_confirmation_checkbox.isChecked()
        prefs['highlights_sent_dialog'] = self.show_count_checkbox.isChecked()
        prefs['web_user'] = self.web_user_checkbox.isChecked()

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
        self.accept()

    def cancel_button(self):
        self.reject()
