from qt.core import QDialog, QVBoxLayout, QPushButton, QMessageBox, QLabel
from calibre.gui2 import info_dialog
from calibre.library import current_library_name
from calibre_plugins.highlights_to_obsidian.config import prefs
from calibre_plugins.highlights_to_obsidian.highlight_sender import HighlightSender
from time import strptime, strftime, localtime, mktime, gmtime


def help_menu(parent):
    title = "Highlights to Obsidian Help Menu"
    body = "You can update the formatting of highlights sent to Obsidian in this plugin's config menu at " + \
           "Preferences -> Plugins -> User interface action -> Highlights to Obsidian.\n\n" + \
           "If you don't want your first time sending new highlights to Obsidian to send all highlights, " + \
           "update the last send time in the config.\n\n" + \
           "Sometimes, if you send highlights while your obsidian vault is closed, not all highlights will " + \
           "be sent. If this happens, you can use the \"Resend Previously Sent Highlights\" function.\n\n" + \
           "You can set keyboard shortcuts in Preferences -> Shortcuts -> H2O. " + \
           "Some available keyboard shortcuts include CTRL+S, CTRL+E, CTRL+G, CTRL+H, CTRL+J, and CTRL+K."
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
        _sender.set_book_titles_authors(book_ids_to_titles_authors(db))
        _sender.set_annotations_list(db.all_annotations())
        _sender.set_sort_key(prefs["sort_key"])
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

        info = f"Success: {amt} highlight{' has' if amt == 1 else 's have'} been sent to obsidian."
        info_dialog(parent, "Highlights Sent", info, show=True)
    else:
        info_dialog(parent, "No Highlights Sent", "No highlights to send.", show=True)

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
    confirm = QMessageBox()
    confirm.setText("Are you sure you want to send ALL highlights to obsidian? This cannot be undone.")
    confirm.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    confirm.setIcon(QMessageBox.Question)
    confirmed = confirm.exec()

    if confirmed == QMessageBox.Yes:
        send_highlights(parent, db)


def resend_highlights(parent, db):
    """
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
