import time
import webbrowser
from typing import Dict, List, Callable, Any, Tuple
from urllib.parse import urlencode, quote
import datetime
# avoid importing anything from calibre or the highlights_to_obsidian plugin here


library_default_name = "Calibre Library"
vault_default_name = "Test"
title_default_format = "Books/{title} by {authors}"
body_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n{notes}\n\n---\n"
no_notes_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n---\n"


def send_item_to_obsidian(obsidian_data: Dict[str, str]) -> None:
    """
    :param obsidian_data: should contain keys and values for 'vault', 'file', 'content', and anything
    else you want to put into the obsidian://new url

    for reference, see https://help.obsidian.md/Advanced+topics/Using+obsidian+URI#Action+new
    """
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


def make_format_dict(data, calibre_library: str, book_titles_authors: Dict[int, Dict[str, str]]) -> Dict:
    """
    :param data: json object of a calibre highlight
    :param calibre_library: name of the calibre library, to make a url to the highlight
    :param book_titles_authors: dictionary mapping book ids to their titles and authors
    :return:
    """

    def format_blockquote(text: str) -> str:
        return "> " + text.replace("\n", "\n> ")

    annot = data["annotation"]

    # calibre's time format example: "2022-09-10T20:32:08.820Z"
    # "%Y-%m-%dT%H:%M:%S", take [:19] of the timestamp to remove milliseconds
    h_time = datetime.datetime.strptime(annot["timestamp"][:19], "%Y-%m-%dT%H:%M:%S")

    # format is calibre://view-book/<Library_Name>/<book_id>/<book_format>?open_at=<location>
    # for example, calibre://view-book/Calibre_Library/39/EPUB?open_at=epubcfi(/8/2/4/84/1:184)
    # todo: right now, opening two different links from the same book opens two different viewer windows,
    # make it instead go to the right location in the already-open window
    url_format = "calibre://view-book/{library}/{book_id}/{book_format}?open_at=epubcfi({location})"
    url_args = {
        "library": calibre_library.replace(" ", "_"),
        "book_id": data["book_id"],
        "book_format": data["format"],
        # the algorithm for this, "/{2 * (spine_index + 1)}", is taken from:
        # read_book.annotations.AnnotationsManager.cfi_for_highlight(uuid, spine_index)
        # https://github.com/kovidgoyal/calibre/blob/master/src/pyj/read_book/annotations.pyj#L249
        # i didn't import the algorithm from calibre because it was too inconvenient to figure out how
        #
        # unfortunately, this doesn't work without the spine index thing. the location is missing a number.
        # it should be, for example /8/2/4/84/1:184, but instead, data["start_cfi"] is /2/4/84/1:184.
        # the first number in the cfi address has to be manually calculated.
        "location": "/" + str((annot["spine_index"] + 1) * 2) + annot["start_cfi"],
    }

    local = time.localtime()
    title_authors = book_titles_authors.get(int(data["book_id"]), {})

    format_options = {
        # if you add a key to this dict, also update the format_options local variable in config.py
        "title": title_authors.get("title", "Untitled"),  # title of book
        "authors": title_authors.get("authors", ("Unknown",)),  # title of book
        "highlight": annot["highlighted_text"],  # highlighted text
        "blockquote": format_blockquote(annot["highlighted_text"]),  # block-quoted highlight
        "notes": annot["notes"] if "notes" in annot else "",  # user's notes on this highlight
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
        "uuid": annot["uuid"],  # highlight's ID in calibre
        "sort_key": h_time.timestamp()  # used to determine order to send highlights in
    }

    return format_options


class HighlightSender:

    def __init__(self):
        # set defaults
        self.library_name = library_default_name
        self.vault_name = vault_default_name
        self.title_format = title_default_format
        self.body_format = body_default_format
        self.no_notes_format = no_notes_default_format
        self.book_titles_authors = {}
        self.annotations_list = []

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

    def set_book_titles_authors(self, book_titles_authors: Dict[int, Dict[str, str]]):
        """
        :param book_titles_authors: dictionary of {book_id: dict of {"title": book_title, "authors": book_authors}},
         to be used for note formatting
        """

        self.book_titles_authors = book_titles_authors

    def set_annotations_list(self, annotations_list):
        """
        :param annotations_list: the object returned by calibre.db.cache.Cache.new_api's all_annotations() function
        """
        self.annotations_list = annotations_list

    def make_obsidian_data(self, note_file, note_content):
        """
        :param note_file: title of this note, including relative path
        :param note_content: body of this note
        :return: dictionary which includes vault name, note file/title, note contents.
        return value can be used as input for send_item_to_obsidian().
        """

        obsidian_data: Dict[str, str] = {
            "vault": self.vault_name,
            "file": note_file,
            "content": note_content,
            "append": "true",
        }

        return obsidian_data

    def send(self, condition: Callable[[Any], bool] = lambda x: True):
        """
        sends highlights to obsidian. currently uses the annotations.calibre_annotation_collection
        file to get highlight data.

        condition takes a highlight's json object and returns true if that highlight should be sent to obsidian.
        """

        highlights = filter(lambda a: a.get("annotation", {}).get("type") == "highlight", self.annotations_list)  # annotations["annotations"])
        dats = []  # List[List[obsidian_data, sort_key]]

        for highlight in highlights:
            if highlight["annotation"].get("removed", False):
                continue  # don't try to send highlights that have been removed

            if not condition(highlight):
                continue

            dat = make_format_dict(highlight, self.library_name, self.book_titles_authors)
            formatted = format_data(dat, self.title_format, self.body_format, self.no_notes_format)

            dats.append([formatted, dat["sort_key"]])

        def merge_highlights(data):
            """
            returns a dictionary with formatted highlights merged into a single string for each
            unique formatted note title found in dats

            for reference, format_data() output is a list of [title, body]

            :param data: List[List[format_data() output, sort_key]]
            :return: list of obsidian_data objects, where each unique title from the input is merged into a
            single, sorted item in the output.
            """
            # this function has too many nested index lookups, it could use some simplification

            books = {}  # dict[str, list[list[obsidian_data object, sort_key]]
            for d in data:
                format_dat = d[0]  # list[title, body]
                body_and_sort = [format_dat[1], d[1]]  # [note body, sort key]
                note_title = format_dat[0]
                if note_title in books:
                    books[note_title].append(body_and_sort)
                else:
                    books[note_title] = [body_and_sort]

            # now, books contains lists of unsorted [note body, sort key] objects
            ret = []

            for key in books:
                # sort each book's highlights and then merge them into a single string
                books[key].sort(key=lambda body_sort: body_sort[1])
                ret.append(self.make_obsidian_data(key, "".join([a[0] for a in books[key]])))

            return ret

        # todo: sometimes, if obsidian isn't already open, not all highlights get sent
        for obsidian_dat in merge_highlights(dats):
            send_item_to_obsidian(obsidian_dat)

        return len(dats)
