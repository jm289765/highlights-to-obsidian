import time
import webbrowser
from typing import Dict, List, Callable, Any
from urllib.parse import urlencode, quote
import datetime


# avoid importing anything from the calibre plugin here
library_default_name = "Calibre Library"
vault_default_name = "Test"
title_default_format = "Books/{title}"
body_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n{notes}\n\n---\n"
no_notes_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n---\n"


def send_item_to_obsidian(obsidian_data: Dict[str, str]) -> None:
    encoded_data = urlencode(obsidian_data, quote_via=quote)
    uri = "obsidian://new?" + encoded_data
    webbrowser.open(uri)


def format_data(dat: Dict[str, str], title: str, body: str, no_notes_body: str = None) -> List[str]:
    """
    apply string.format() to title and body with data values from dat. Also removes slashes from title.

    if there are no notes associated with a highlight, then no_notes_body will be used instead of body

    :return: list containing two strings: [formatted title, formatted body]
    """

    def remove_slashes(text: str) -> str:
        # remove slashes in the note's title, since slashes in obsidian note titles will specify a directory
        return text.replace("/", "-").replace("\\", "-")

    def remove_illegal_title_chars(text: str) -> str:
        # illegal title characters characters: * " \ / < > : | ?
        # but we won't remove slashes because they're used for putting the note in a folder
        # these can be title characters, but will break Markdown links to the file: # ^ [ ]
        illegals = '*"<>:|?#^[]'
        ret = text

        for c in illegals:
            ret = ret.replace(c, "")

        return ret

    pre_format = title.replace("{title}", remove_slashes(dat["title"]))
    return [remove_illegal_title_chars(pre_format.format(**dat)),
            body.format(**dat) if no_notes_body and len(dat["notes"]) > 0 else no_notes_body.format(**dat)]


def make_format_dict(data: Dict[str, str], calibre_library: str, book_titles: Dict[int, str]) -> Dict[str, str]:
    """
    :param data: json object of a calibre highlight
    :param calibre_library: name of the calibre library, to make a url to the highlight
    :param book_titles: dictionary mapping book ids to their titles
    :return:
    """

    def format_blockquote(text: str) -> str:
        return "> " + text.replace("\n", "\n> ")

    # calibre's time format example: "2022-09-10T20:32:08.820Z"
    # "%Y-%m-%dT%H:%M:%S", take [:-5] of the timestamp to remove milliseconds
    h_time = datetime.datetime.strptime(data["timestamp"][:-5], "%Y-%m-%dT%H:%M:%S")

    # format is calibre://view-book/<Library_Name>/<book_id>/<book_format>?open_at=<location>
    # for example, calibre://view-book/Calibre_Library/39/EPUB?open_at=epubcfi(/2/4/84/1:184)
    # unfortunately, this doesn't work. the location is missing a number. it should be /8/2/4/84/1:184,
    # where the 8 at the start represents a page number or section or something. instead, it opens
    # the book to the beginning instead of to the highlight. this seems to be a problem of calibre not
    # putting the right location data in its exported annotations.
    # todo: fix calibre:// urls not opening to the correct location in the book
    url_format = "calibre://view-book/{library}/{book_id}/{book_format}?open_at=epubcfi({location})"
    url_args = {
        "library": calibre_library.replace(" ", "_"),
        "book_id": data["book_id"],
        "book_format": data["format"],
        "location": data["start_cfi"],
    }

    local = time.localtime()

    format_options = {
        "title": book_titles.get(int(data["book_id"]), "No Title"),  # title of book
        # todo: add option for author of book
        "highlight": data["highlighted_text"],  # highlighted text
        "blockquote": format_blockquote(data["highlighted_text"]),  # block-quoted highlight
        "notes": data["notes"] if "notes" in data else "",  # user's notes on this highlight
        "date": str(h_time.date()),  # date highlight was made
        "time": str(h_time.time()),  # time highlight was made
        "datetime": str(h_time),
        # calibre uses local time when making annotations. see function "render_timestamp"
        # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/gui2/library/annotations.py#L34
        # todo: timezone currently displays "Coordinated Universal Time" instead of the abbreviation, "UTC"
        "timezone": local.tm_zone,
        "timeoffset": ("-" if local.tm_gmtoff < 0 else "+") + str(local.tm_gmtoff // 3600) + ":00",
        "day": str(h_time.day),
        "month": str(h_time.month),
        "year": str(h_time.year),
        "url": url_format.format(**url_args),  # calibre:// url to open ebook viewer to this highlight
        "bookid": data["book_id"],
        "uuid": data["uuid"],  # highlight's ID in calibre
    }

    return format_options


class HighlightSender:

    def __init__(self):
        # todo: remove this variable
        self.calibre_annotations_path = \
            r"C:\Users\Admin\Documents\Github\highlights-to-obsidian\annotations.calibre_annotation_collection"

        # set defaults
        self.library_name = library_default_name
        self.vault_name = vault_default_name
        self.title_format = title_default_format
        self.body_format = body_default_format
        self.no_notes_format = no_notes_default_format
        self.book_titles = {}

        # highlight send condition variable
        # highlights json object variable

    def set_library(self, library_name: str):
        self.library_name = library_name

    def set_vault(self, vault_name: str):
        self.vault_name = vault_name

    def set_title_format(self, title_format: str):
        self.title_format = title_format

    def set_body_format(self, body_format: str):
        self.body_format = body_format

    def set_no_notes_format(self, no_notes_format: str):
        """
        sets the body format to be used for highlights that the user didn't make notes for
        """
        self.no_notes_format = no_notes_format

    def set_book_titles(self, book_titles: Dict[int, str]):
        """
        :param book_titles: dictionary of {book_id: book_title}, to be used for note formatting
        """
        self.book_titles = book_titles

    def send(self, condition: Callable[[Any], bool] = lambda x: True):
        """
        sends highlights to obsidian. currently uses the annotations.calibre_annotation_collection
        file to get highlight data.

        condition takes a highlight's json object and returns true if that highlight should be sent to obsidian.
        """
        # encoding has to be 'utf-8-sig' because calibre annotation files use BOM
        # todo: get annotations directly from calibre
        file = open(self.calibre_annotations_path, encoding='utf-8-sig')

        from json import load
        annotations = load(file, parse_int=str, parse_float=str, parse_constant=str)

        highlights = filter(lambda a: a["type"] == "highlight", annotations["annotations"])

        for highlight in highlights:
            if not condition(highlight):
                continue

            dat = make_format_dict(highlight, self.library_name, self.book_titles)
            formatted = format_data(dat, self.title_format, self.body_format, self.no_notes_format)

            obsidian_data: Dict[str, str] = {
                "vault": self.vault_name,
                "file": formatted[0],
                "content": formatted[1],
                "append": "true",
            }

            send_item_to_obsidian(obsidian_data)

        # todo: return number of highlights sent, and use that as output for main.py


x = HighlightSender()
