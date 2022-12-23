from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre_plugins.highlights_to_obsidian.config import prefs
from calibre_plugins.highlights_to_obsidian.send import send_highlights
from time import strptime, strftime, localtime, mktime


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

        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.conf_button = QPushButton(
            'Configure this plugin', self)
        self.conf_button.clicked.connect(self.config)
        self.l.addWidget(self.conf_button)

        self.send_button = QPushButton("Send new highlights to obsidian", self)
        self.send_button.clicked.connect(self.send_new_highlights)
        self.l.addWidget(self.send_button)

        self.send_all_button = QPushButton("Send all highlights to obsidian", self)
        # todo: add a confirmation dialog to this
        self.send_all_button.clicked.connect(self.send_all_highlights)
        self.l.addWidget(self.send_all_button)

        self.resize(self.sizeHint())

    # todo: remove unused functions: about(), marked(), view(), update_metadata()
    def about(self):
        # Get the about text from a file inside the plugin zip file
        # The get_resources function is a builtin function defined for all your
        # plugin code. It loads files from the plugin zip file. It returns
        # the bytes from the specified file.
        #
        # Note that if you are loading more than one file, for performance, you
        # should pass a list of names to get_resources. In this case,
        # get_resources will return a dictionary mapping names to bytes. Names that
        # are not found in the zip file will not be in the returned dictionary.
        text = get_resources('about.txt')
        QMessageBox.about(self, 'Last Time Highlights Were Sent',
                          prefs["last_send_time"])
        # text.decode('utf-8'))

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
        # if any config changes require updating this

    def send_new_highlights(self):
        last_send_time = mktime(strptime(prefs["last_send_time"], "%Y-%m-%d %H:%M:%S"))

        def highlight_send_condition(highlight) -> bool:
            """
            :param highlight: json object containing a calibre highlight's data
            :return: true if the highlight was made after last send time, else false
            """
            # an alternative method is to save the uuid of each highlight as it's sent,
            # then save that list in prefs.

            # calibre's time format example: "2022-09-10T20:32:08.820Z"
            highlight_time = mktime(strptime(highlight["timestamp"][:-5], "%Y-%m-%dT%H:%M:%S"))
            return highlight_time > last_send_time

        # send_highlights(title_format, body_format, no_notes_format, vault_name, library_name, condition)
        send_highlights(prefs['title_format'], prefs['body_format'], vault_name=prefs['vault_name'],
                        condition=highlight_send_condition)

        # updating prefs might belong in menu_button.py's apply_settings function, idk
        prefs["last_send_time"] = strftime("%Y-%m-%d %H:%M:%S", localtime())

        # todo: add something to tell the user that highlights have been sent
        # maybe a QMessageBox

    def send_all_highlights(self):

        # send_highlights(title_format, body_format, no_notes_format, vault_name, library_name, condition)
        send_highlights(prefs['title_format'], prefs['body_format'], vault_name=prefs['vault_name'])

        # updating prefs might belong in menu_button.py's apply_settings function, idk
        prefs["last_send_time"] = strftime("%Y-%m-%d %H:%M:%S", localtime())

        # todo: add something to tell the user that highlights have been sent
