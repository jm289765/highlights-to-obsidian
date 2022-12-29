from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre.gui2 import info_dialog
from calibre.library import current_library_name
from calibre_plugins.highlights_to_obsidian.config import prefs
from calibre_plugins.highlights_to_obsidian.send import HighlightSender
from time import strptime, strftime, localtime, mktime


class MainDialog(QDialog):

    def __init__(self, gui, icon, do_user_config):
        # todo: if this is the first time the extension has been used, open a popup telling the
        # user to set config and, if they don't want to send all notes, last_send_time.
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

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        # button to open config
        self.conf_button = QPushButton(
            'Configure this plugin', self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        # send new highlights button
        self.send_button = QPushButton("Send new highlights to obsidian", self)
        self.send_button.clicked.connect(self.send_new_highlights)
        self.l.addWidget(self.send_button)

        # send all highlights button
        self.send_all_button = QPushButton("Send all highlights to obsidian", self)
        self.send_all_button.clicked.connect(self.send_all_highlights)
        self.l.addWidget(self.send_all_button)

        # resend previously sent highlights button
        self.resend_button = QPushButton("Resend previously sent highlights", self)
        self.resend_button.clicked.connect(self.resend_highlights)
        self.l.addWidget(self.resend_button)

        self.resize(self.sizeHint())

    def config(self):
        self.do_user_config(parent=self)
        # if any config changes require updating self, do it here

    def send_highlights(self, condition=lambda x: True, update_send_time=True) -> int:
        """

        :param condition: condition for sending a highlight
        :param update_send_time: whether or not to update prefs["last_send_time"]
        :return: number of highlights that were sent
        """

        def make_sender() -> HighlightSender:
            _sender = HighlightSender()
            # this might not work if the current library name has characters that don't work in urls.
            # but if do hex encoding when it's not needed, i'll make links hard to read.
            # todo: add hex encoding, but only when necessary https://manual.calibre-ebook.com/url_scheme.html
            _sender.set_library(current_library_name())
            _sender.set_vault(prefs["vault_name"])
            _sender.set_title_format(prefs["title_format"])
            _sender.set_body_format(prefs["body_format"])
            _sender.set_no_notes_format(prefs["no_notes_format"])
            _sender.set_book_titles_authors(self.book_ids_to_titles_authors())
            db = self.db.new_api
            _sender.set_annotations_list(db.all_annotations())
            return _sender

        sender = make_sender()
        amt = sender.send(condition=condition)

        if amt > 0:
            # don't update send time if no highlights were actually sent. this makes sure you
            # won't mess up your prev_send if you accidentally send new highlights twice in a row.
            if update_send_time:
                prefs["last_send_time"] = strftime("%Y-%m-%d %H:%M:%S", localtime())

            info = f"Success: {amt} highlight{' has' if amt == 1 else 's have'} been sent to obsidian."
            info_dialog(self, "Highlights Sent", info, show=True)
        else:
            info_dialog(self, "No Highlights Sent", "No highlights to send.", show=True)

        return amt

    def send_new_highlights(self):
        last_send_time = mktime(strptime(prefs["last_send_time"], "%Y-%m-%d %H:%M:%S"))

        def highlight_send_condition(highlight) -> bool:
            """
            :param highlight: json object containing a calibre highlight's data
            :return: true if the highlight was made after last send time, else false
            """
            # an alternative method is to save the uuid of each highlight as it's sent,
            # then save that list in prefs, then check if the highlight is in that list

            # calibre's time format example: "2022-09-10T20:32:08.820Z"
            highlight_time = mktime(strptime(highlight["annotation"]["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
            return highlight_time > last_send_time

        new_prev_send = prefs["last_send_time"]
        amt_sent = self.send_highlights(highlight_send_condition)
        if amt_sent > 0:
            prefs["prev_send"] = new_prev_send

    def send_all_highlights(self):
        confirm = QMessageBox()
        confirm.setText("Are you sure you want to send ALL highlights to obsidian? This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setIcon(QMessageBox.Question)
        confirmed = confirm.exec()

        if confirmed == QMessageBox.Yes:
            self.send_highlights()

    def resend_highlights(self):
        """
        this function is mainly intended to be used in case obsidian fails to receive the highlights that
        were sent to it. this sometimes happens when the obsidian program isn't open to the right vault
        or isn't open at all when highlights are sent. it also sometimes happens for reasons unknown to me.
        """
        prev_send = prefs['prev_send']
        if prev_send is None:
            info_dialog(self, "Cannot resend highlights", "No highlights were previously sent", show=True)
            return

        # prev_send is the date/time of the send time before last_send_time.
        # send highlights between then and last_send_time.
        prev_send_time = mktime(strptime(prefs["prev_send"], "%Y-%m-%d %H:%M:%S"))
        last_send_time = mktime(strptime(prefs["last_send_time"], "%Y-%m-%d %H:%M:%S"))

        def highlight_send_condition(highlight) -> bool:
            """
            :param highlight: json object containing a calibre highlight's data
            :return: true if the highlight was made between prev send time and most recent send time
            """
            # alternatively, store the uuids of previously sent highlights in prefs, and only send those

            # calibre's time format example: "2022-09-10T20:32:08.820Z"
            highlight_time = mktime(strptime(highlight["annotation"]["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
            return prev_send_time < highlight_time < last_send_time

        self.send_highlights(highlight_send_condition, update_send_time=False)

    def book_ids_to_titles_authors(self):

        def format_authors(authors) -> str:
            """
            :param authors: Tuple[str] with author names in it
            :return: author names merged into a single string
            """
            auths = list(authors)
            if len(auths) > 1:
                auths[-1] = "and " + auths[-1]

            return ", ".join(auths) if len(auths) > 2 else " " .join(auths)

        ret = {}
        db = self.db.new_api

        for book_id, title in db.all_field_for('title', db.all_book_ids()).items():
            authors = format_authors(db.field_for("authors", book_id))
            ret[book_id] = {"title": title, "authors": authors}

        return ret
