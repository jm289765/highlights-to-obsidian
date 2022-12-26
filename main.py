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

        # test button
        self.test_button = QPushButton("Test", self)
        self.test_button.clicked.connect(self.test)
        self.l.addWidget(self.test_button)

        # send new highlights button
        self.send_button = QPushButton("Send new highlights to obsidian", self)
        self.send_button.clicked.connect(self.send_new_highlights)
        self.l.addWidget(self.send_button)

        # send all highlights button
        self.send_all_button = QPushButton("Send all highlights to obsidian", self)
        # todo: add a confirmation dialog to this
        self.send_all_button.clicked.connect(self.send_all_highlights)
        self.l.addWidget(self.send_all_button)

        self.resize(self.sizeHint())

    # todo: remove unused functions: marked(), view(), update_metadata()

    def marked(self):
        ''' Show books with only one format '''
        db = self.db.new_api
        matched_ids = {book_id for book_id in db.all_book_ids() if len(db.formats(book_id)) == 1}
        # Mark the records with the matching ids
        # new_api does not know anything about marked books, so we use the full
        # db object
        self.db.set_marked_ids(matched_ids)

        # Tell the GUI to search for all marked records
        self.gui.search.setEditText('marked:true')
        self.gui.search.do_search()

    def view(self):
        ''' View the most recently added book '''
        most_recent = most_recent_id = None
        db = self.db.new_api
        for book_id, timestamp in db.all_field_for('timestamp', db.all_book_ids()).items():
            if most_recent is None or timestamp > most_recent:
                most_recent = timestamp
                most_recent_id = book_id

        if most_recent_id is not None:
            # Get a reference to the View plugin
            view_plugin = self.gui.iactions['View']
            # Ask the view plugin to launch the viewer for row_number
            view_plugin._view_calibre_books([most_recent_id])

    def update_metadata(self):
        '''
        Set the metadata in the files in the selected book's record to
        match the current metadata in the database.
        '''
        from calibre.ebooks.metadata.meta import set_metadata
        from calibre.gui2 import error_dialog, info_dialog

        # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, 'Cannot update metadata',
                                'No books selected', show=True)
        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        db = self.db.new_api
        for book_id in ids:
            # Get the current metadata for this book from the db
            mi = db.get_metadata(book_id, get_cover=True, cover_as_data=True)
            fmts = db.formats(book_id)
            if not fmts:
                continue
            for fmt in fmts:
                fmt = fmt.lower()
                # Get a python file object for the format. This will be either
                # an in memory file or a temporary on disk file
                ffile = db.format(book_id, fmt, as_file=True)
                ffile.seek(0)
                # Set metadata in the format
                set_metadata(ffile, mi, fmt)
                ffile.seek(0)
                # Now replace the file in the calibre library with the updated
                # file. We dont use add_format_with_hooks as the hooks were
                # already run when the file was first added to calibre.
                db.add_format(book_id, fmt, ffile, run_hooks=False)

        info_dialog(self, 'Updated files',
                    'Updated the metadata in the files of %d book(s)' % len(ids),
                    show=True)

    def config(self):
        self.do_user_config(parent=self)
        # if any config changes require updating self, do it here

    def send_highlights(self, condition=lambda x: True):
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
            _sender.set_book_titles(self.book_ids_to_titles())
            return _sender

        sender = make_sender()
        sender.send(condition=condition)

        # updating prefs might belong in menu_button.py's apply_settings function, idk
        prefs["last_send_time"] = strftime("%Y-%m-%d %H:%M:%S", localtime())

        info_dialog(self, "Highlights Sent",
                    "New highlights have been sent to obsidian.",
                    show=True)

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
            highlight_time = mktime(strptime(highlight["timestamp"][:-5], "%Y-%m-%dT%H:%M:%S"))
            return highlight_time > last_send_time

        self.send_highlights(highlight_send_condition)

    def send_all_highlights(self):
        self.send_highlights()

    def book_ids_to_titles(self):
        ret = {}
        db = self.db.new_api

        for book_id, title in db.all_field_for('title', db.all_book_ids()).items():
            ret[book_id] = title

        return ret

    def test(self):
        info_dialog(self, "Test", "Test info dialog", show=True)
