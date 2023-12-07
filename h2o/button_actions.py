from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre.gui2 import info_dialog
from calibre.library import current_library_name
from calibre_plugins.highlights_to_obsidian.config import prefs
from calibre_plugins.highlights_to_obsidian.highlight_sender import HighlightSender
from time import strptime, strftime, mktime, gmtime


def help_menu(parent):
    title = "Highlights to Obsidian Help Menu"
    body = "You can update the formatting of highlights sent to Obsidian in this plugin's config menu at " + \
           "Preferences -> Plugins -> User interface action -> Highlights to Obsidian.\n\n" + \
           "If you don't want the first time sending new highlights to Obsidian to send all highlights, " + \
           "update the last send time in the config.\n\n" + \
           "In the formatting config menu, the 'title' is the title of the note that a highlight will be " + \
           "sent to. The 'body' is the text that will be sent to that note for each highlight. The " + \
           "'header' will be sent to each note exactly once when you send highlights.\n\n" + \
           "In a note's title, you can include slashes \"/\" to specify what folder the note should be in.\n\n" + \
           "Sometimes, if you send highlights while your obsidian vault is closed, not all highlights will " + \
           "be sent. If this happens, you can use the \"Resend Previously Sent Highlights\" function.\n\n" + \
           "You can set keyboard shortcuts in calibre's Preferences -> Shortcuts -> H2O.\n\n" + \
           "Due to URI length limits, H2O can only send a few thousand words to a single note at once. Extra text " \
           "will be sent to different notes with increasing numbers added to the end of the title.\n\n" + \
           "If you're using Linux and H2O opens your web browser instead of Obsidian, see the xdg-open setting " + \
           "at the bottom of the config's Other Options."
    info_dialog(parent, title, body, show=True)


def send_highlights(parent, db, condition=lambda x: True, update_send_time=True) -> int:
    """
    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
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
        _sender.set_header_format(prefs["header_format"] if prefs["use_header"] else "")
        _sender.set_book_titles_authors(book_ids_to_titles_authors(db))
        _sender.set_sort_key(prefs["sort_key"])
        _sender.set_sleep_time(prefs["sleep_secs"])
        if prefs['use_max_note_size']:
            _sender.set_max_file_size(int(prefs['max_note_size']), prefs['copy_header'])

        """ all_annotations() and all_annotation_users()
         https://github.com/kovidgoyal/calibre/blob/master/src/calibre/db/cache.py
         
        some possible values for restrict_to_user
         https://github.com/kovidgoyal/calibre/blob/master/src/calibre/gui2/library/annotations.py#L138 """
        # todo: i could replace some logic (e.g. filtering by book id) by using the parameters of db.all_annotations()
        user = ("web", prefs["web_user_name"]) if prefs["web_user"] else ("local", "viewer")
        _sender.set_annotations_list(db.all_annotations(restrict_to_user=user))
        return _sender

    sender = make_sender()
    amt = sender.send(condition=condition)

    if amt > 0:
        # don't update send time if no highlights were actually sent. this makes sure you
        # won't mess up your prev_send if you accidentally send new highlights twice in a row.
        if update_send_time:
            # has to be time.gmtime() so that we use utc. calibre stores highlight time as UTC, and last_send_time
            # is what we compare to. if you use localtime instead of gmtime, you'll get rare bugs when the computer's
            # timezone changes.
            prefs["last_send_time"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        info = f"Success: {amt} highlight{' has' if amt == 1 else 's have'} been sent to Obsidian."
        if prefs['highlights_sent_dialog']:
            info_dialog(parent, "Highlights Sent", info, show=True)
    else:
        info_dialog(parent, "No Highlights Sent", "There are no highlights to send.", show=True)

    return amt


def send_new_highlights(parent, db):
    """
    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    """
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
    amt_sent = send_highlights(parent, db, highlight_send_condition)
    if amt_sent > 0:
        prefs["prev_send"] = new_prev_send


def send_all_highlights(parent, db):
    """
    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    """
    if prefs['confirm_send_all']:
        confirm = QMessageBox()
        confirm.setText("Are you sure you want to send ALL highlights to Obsidian? This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setIcon(QMessageBox.Question)
        confirmed = confirm.exec()

        if confirmed != QMessageBox.Yes:
            return

    send_highlights(parent, db)


def send_new_selected_highlights(parent, db):
    """
    sends new highlights in the currently selected books in the main window. does update last_send_time, so
    any new highlights not in the selected books will be ignored, but can be sent with resend_highlights

    :param parent: QDialog or other window that is the parent of the info dialogs this function makes. should be, or
    have as a property ".gui", calibre's gui object.
    :param db: calibre database: Cache().new_api
    """

    try:
        parent.library_view  # check if this exists
        gui = parent
    except:
        gui = parent.gui

    rows = gui.library_view.selectionModel().selectedRows()
    selected_ids = list(map(gui.library_view.model().id, rows))
    last_send_time = mktime(strptime(prefs["last_send_time"], "%Y-%m-%d %H:%M:%S"))

    def highlight_send_condition(highlight):
        # todo: probably a good idea to move the last_send_time check to an external function, since the code is
        #  repeated in 3 places: send_new_selected_highlights, send_new_highlights, resend_highlights
        highlight_time = mktime(strptime(highlight["annotation"]["timestamp"][:19], "%Y-%m-%dT%H:%M:%S"))
        return highlight_time > last_send_time and int(highlight["book_id"]) in selected_ids

    send_highlights(parent, db, highlight_send_condition, update_send_time=True)


def send_all_selected_highlights(parent, db):
    """
    sends all highlights in the currently selected books in the main window.

    :param parent: QDialog or other window that is the parent of the info dialogs this function makes. should be, or
    have as a property ".gui", calibre's gui object.
    :param db: calibre database: Cache().new_api
    """

    if prefs['confirm_send_all']:
        confirm = QMessageBox()
        confirm.setText("Are you sure you want to send ALL highlights of the selected books to Obsidian? This cannot be undone.")
        confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm.setIcon(QMessageBox.Question)
        confirmed = confirm.exec()

        if confirmed != QMessageBox.Yes:
            return

    try:
        parent.library_view  # check if this exists
        gui = parent
    except:
        gui = parent.gui

    rows = gui.library_view.selectionModel().selectedRows()
    selected_ids = list(map(gui.library_view.model().id, rows))

    def highlight_send_condition(highlight):
        return int(highlight["book_id"]) in selected_ids

    send_highlights(parent, db, highlight_send_condition, update_send_time=False)


def resend_highlights(parent, db):
    """
    resends highlights that were previously sent with send_new_highlights.

    this function is mainly intended to be used in case obsidian fails to receive the highlights that
    were sent to it. this sometimes happens when the obsidian program isn't open to the right vault
    or isn't open at all when highlights are sent. it also sometimes happens for reasons unknown to me.

    :param parent: QDialog or other window that is the parent of the info dialogs this function makes
    :param db: calibre database: Cache().new_api
    """
    prev_send = prefs['prev_send']
    if prev_send is None:
        info_dialog(parent, "Cannot resend highlights", "No highlights were previously sent", show=True)
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

    send_highlights(parent, db, condition=highlight_send_condition, update_send_time=False)


def book_ids_to_titles_authors(db):

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

    for book_id, title in db.all_field_for('title', db.all_book_ids()).items():
        authors = format_authors(db.field_for("authors", book_id))
        ret[book_id] = {"title": title, "authors": authors}

    return ret
