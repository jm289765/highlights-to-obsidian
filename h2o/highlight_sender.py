import time
import webbrowser
from typing import Dict, List, Callable, Any, Tuple, Iterable, Union
from urllib.parse import urlencode, quote
import datetime
import re as regex

# avoid importing anything from calibre or the highlights_to_obsidian plugin here


# might be better to move these into resource files
library_default_name = "Calibre Library"
vault_default_name = "My Vault"
title_default_format = "Books/{title} by {authors}"
body_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC:\n{blockquote}\n\n{notes}\n\n---\n"
no_notes_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC:\n{blockquote}\n\n---\n"
header_default_format = "\n{booksent} highlights from \"{title}\" sent on {datenow} at {timenow} UTC.\n\n---\n"

sort_key_default = "location"


def send_item_to_obsidian(obsidian_data: Dict[str, str]) -> None:
    """
    :param obsidian_data: should contain keys and values for 'vault', 'file', 'content', and anything
    else you want to put into the obsidian://new url

    for reference, see https://help.obsidian.md/Advanced+topics/Using+obsidian+URI#Action+new
    """
    encoded_data = urlencode(obsidian_data, quote_via=quote)
    uri = "obsidian://new?" + encoded_data
    try:
        webbrowser.open(uri)
    except ValueError as e:
        raise ValueError(f" send_item_to_obsidian: '{e}' in note '{obsidian_data['file']}'.\n\n"
                         f"If this error says that the filepath is too long, try reducing the max file size in "
                         f"the Highlights to Obsidian config (the path length that caused this error is {len(uri)}. "
                         f"The path size will be larger than the max file size due to URL encoding).")


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

    # use format_map instead of format so that we leave invalid placeholders, e.g. if a highlight contains curly
    # brackets, we don't want to replace the part in the highlight (it'll still be replaced if the highlight contains
    # a valid placeholder though).
    pre_format = title.replace("{title}", remove_slashes(dat["title"]))
    return [remove_illegal_title_chars(pre_format.format_map(dat)),
            body.format_map(dat) if no_notes_body and len(dat["notes"]) > 0 else no_notes_body.format_map(dat)]


def format_single(dat: Dict[str, str], item_format: str) -> str:
    """
    returns item_format.format_map(dat)

    :param dat: output of make_format_dict. dict containing keys and values for string formatting.
    :param item_format: string to be formatted
    :return: string with formatted item
    """
    # use format_map instead of format so that we leave invalid placeholders, e.g. if a highlight contains curly
    # brackets, we don't want to replace the part in the highlight (it'll still be replaced if the highlight contains
    # a valid placeholder though).
    return item_format.format_map(dat)


def make_time_format_dict(data: Dict) -> Dict[str, str]:
    """

    :param data: json object of a calibre highlight
    :return: dict containing all time-related formatting options
    """

    annot = data["annotation"]

    # calibre's time format example: "2022-09-10T20:32:08.820Z"
    # the "Z" at the end means UTC time
    # "%Y-%m-%dT%H:%M:%S", take [:19] of the timestamp to remove milliseconds
    # better alternative might be dateutil.parser.parse
    h_time = datetime.datetime.strptime(annot["timestamp"][:19], "%Y-%m-%dT%H:%M:%S")
    h_local = h_time + h_time.astimezone(datetime.datetime.now().tzinfo).utcoffset()
    local = time.localtime()
    utc = time.gmtime()
    utc_offset = ("" if local.tm_gmtoff < 0 else "+") + str(local.tm_gmtoff // 3600) + ":00"

    time_options = {
        "date": str(h_time.date()),  # utc date highlight was made
        "localdate": str(h_local.date()),
        # local date highlight was made. "local" based on send time, not highlight time
        "time": str(h_time.time()),  # utc time highlight was made
        "localtime": str(h_local.time()),  # local time highlight was made
        "datetime": str(h_time),
        "localdatetime": str(h_local),
        # calibre uses local time when making annotations. see function "render_timestamp"
        # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/gui2/library/annotations.py#L34
        # todo: timezone currently displays "Coordinated Universal Time" instead of the abbreviation, "UTC"
        "timezone": h_local.tzname(),  # local timezone
        "localtimezone": h_local.tzname(),  # so that the config menu's explanation doesn't confuse users
        "utcoffset": utc_offset,
        "localoffset": utc_offset,  # so that the config menu's explanation doesn't confuse users
        "timeoffset": utc_offset,  # for backwards compatibility
        "day": f"{h_time.day:02}",
        "localday": f"{h_local.day:02}",
        "month": f"{h_time.month:02}",
        "localmonth": f"{h_local.month:02}",
        "year": f"{h_time.year:04}",
        "localyear": f"{h_local.year:04}",
        "hour": f"{h_time.hour:02}",
        "localhour": f"{h_local.hour:02}",
        "minute": f"{h_time.minute:02}",
        "localminute": f"{h_local.minute:02}",
        "second": f"{h_time.second:02}",
        "localsecond": f"{h_local.second:02}",
        "utcnow": time.strftime("%Y-%m-%d %H:%M:%S", utc),
        "datenow": time.strftime("%Y-%m-%d", utc),
        "timenow": time.strftime("%H:%M:%S", utc),
        "localnow": time.strftime("%Y-%m-%d %H:%M:%S", local),
        "localdatenow": time.strftime("%Y-%m-%d", local),
        "localtimenow": time.strftime("%H:%M:%S", local),
        "timestamp": str(h_time.timestamp()),  # Unix timestamp of highlight time. uses UTC.
    }

    return time_options


def make_highlight_format_dict(data: Dict, calibre_library: str) -> Dict[str, str]:
    """

    :param data: json object of a calibre highlight
    :param calibre_library: name of library book is found in. used for making a url to the highlight.
    :return: dict containing all highlight-related formatting options.
    """

    def format_blockquote(text: str) -> str:
        return "> " + text.replace("\n", "\n> ")

    annot = data["annotation"]

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

    highlight_format = {
        "highlight": annot["highlighted_text"],  # highlighted text
        "blockquote": format_blockquote(annot["highlighted_text"]),  # block-quoted highlight
        "notes": annot["notes"] if "notes" in annot else "",  # user's notes on this highlight
        "url": url_format.format(**url_args),  # calibre:// url to open ebook viewer to this highlight
        "location": url_args["location"],  # epub cfi location of this highlight
        "uuid": annot["uuid"],  # highlight's ID in calibre
    }

    return highlight_format


def make_book_format_dict(data: Dict, book_titles_authors: Dict[int, Dict[str, str]]) -> Dict[str, str]:
    """

    :param data: json object of a calibre highlight
    :param book_titles_authors: dictionary mapping book ids to {"title": title, "authors": authors}
    :return: dict containing all book-related formatting options
    """
    title_authors = book_titles_authors.get(int(data["book_id"]), {})  # dict with {"title": str, "authors": Tuple[str]}

    format_options = {
        "title": title_authors.get("title", "Untitled"),  # title of book
        # todo: add "chapter" option
        "authors": title_authors.get("authors", ("Unknown",)),  # authors of book
        "bookid": data["book_id"],
    }

    return format_options


def make_sent_format_dict(total_sent, book_sent, highlight_sent) -> Dict[str, str]:
    """
    inputs will be converted to strings.

    :param total_sent: total number of highlights being sent
    :param book_sent: total number of highlights being sent for this book
    :param highlight_sent: this highlight's position in the highlights being sent to this book, e.g. 5 if it's
     the fifth highlight.
    :return: dict containing a format option for each of the params
    """
    sent_dict = SafeDict()
    sent_dict["totalsent"] = str(total_sent)  # total highlights sent
    sent_dict["booksent"] = str(book_sent)  # highlights for this book
    sent_dict["highlightsent"] = str(highlight_sent)  # position of this highlight

    return sent_dict


def make_format_dict(data, calibre_library: str, book_titles_authors: Dict[int, Dict[str, str]]) -> Dict[str, str]:
    """
    :param data: json object of a calibre highlight
    :param calibre_library: name of the calibre library, to make a url to the highlight
    :param book_titles_authors: dictionary mapping book ids to {"title": title, "authors": authors}
    :return: dict[str, str] containing formatting options
    """

    # formatting options are based on https://github.com/jplattel/obsidian-clipper

    # todo: could be optimized by taking as input the formatting options that are needed, and then
    #  only calculating values for those options

    # if you add a format option, also update the format_options local variable in config.py and the docs in README.md
    time_options = make_time_format_dict(data)
    highlight_options = make_highlight_format_dict(data, calibre_library)
    book_options = make_book_format_dict(data, book_titles_authors)

    # these formatting options can't be calculated by the time make_format_dict is called.
    # actually, totalsent probably could be, but let's keep it here with the others.
    # we need to include this so that string.format() doesn't error if it runs into one of these
    placeholders = make_sent_format_dict("{totalsent}", "{booksent}", "{highlightsent}")

    # the | operator merges dictionaries https://peps.python.org/pep-0584/
    # could also pass a dict as a param to each make_x_dict, and have them update it in place
    return SafeDict(**time_options, **highlight_options, **book_options, **placeholders)


class SafeDict(dict):
    def __init__(self, **kwargs):
        """if a key is not found in this dict, will return the key with {curly brackets}.

        useful for making str.format() ignore invalid keys without changing the input string."""
        super().__init__(kwargs)

    def __missing__(self, key):
        return "{" + key + "}"


class BookData:
    # todo: refactor: make a BookData class to store data of book title(s), highlight, length, count, etc
    #  BookData: fields for title, header, list of notes and sort keys or dict of {sort_key: note}?
    #            functions for formatting title, header, etc
    #  BookList: holds a dict of string titles of books with a BookData for each one.
    #            functions for add(title, BookData), split long dataset into multiple books, get base title
    #                of a split book, etc
    def __init__(self, title: str, header: str = None, notes: List[List[Union[str, Any]]] = None):
        """

        :param title: book's title
        :param header: header to be used when notes are sent to Obsidian
        :param notes: list of [note_content, sort_key]
        """

        self._title = title
        self._header = header
        if notes is not None:
            self.notes: List[List[Union[str, Any]]] = list(sorted(notes, key=lambda n: n[1]))
        else:
            self.notes: List[List[Union[str, Any]]] = []  # List[List[note:str, sort_key:Any]]

    def __len__(self):
        """ number of notes that this book has """
        return len(self.notes)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, title: str) -> None:
        """
        warning: when possible, use BookList's update_title() instead. if you update the title directly, BookList
         will keep the old title as the key in its dict of BookData objects.
        """
        self._title = title

    @property
    def header(self) -> str:
        return self._header

    @header.setter
    def header(self, header: str) -> None:
        self._header = header

    def add_note(self, note: str, sort_key: Any = None) -> None:
        """
        :param note: text of note to add to this book's notes
        :param sort_key: sort key to use when merging book's notes into a single string
        :return: none
        """
        self.insort_note([note, sort_key])

    def update_note(self, idx: int, new_note: str) -> None:
        self.notes[idx][0] = new_note

    def insort_note(self, note: List[Union[str, Any]]):
        """ copied and modified from bisect.insort_right(...)

        Insert note into self.notes, and keep it sorted based on sort_key.
        Assumes that the note is not already in self.notes.
        If sort_key is None, append the note to self.notes.
        """
        sort_key = note[1]
        if sort_key is None:
            self.notes.append(note)
            return

        lo, hi = 0, len(self.notes)
        while lo < hi:
            mid = (lo + hi) // 2
            if sort_key < self.notes[mid][1]:
                hi = mid
            else:
                lo = mid + 1
        self.notes.insert(lo, note)

    def make_sendable_notes(self, max_size: int = -1, copy_header: bool = False) -> Iterable[Tuple[str, str]]:
        """
        merges this book's notes into a single string.

        This limits the length of merged note contents to max_size. If the length exceeds this, extra
        highlights will use a different title, e.g. "The Book", "The Book (1)", etc

        :param max_size: maximum allowed size of a note (notes might be longer after headers are added)
        :param copy_header: if a single note is split into multiple, should the header be copied into each one,
        or should only the first note have a header?
        :return: yields an iterable of tuples of (title, contents) pairs
        """

        if max_size == -1:
            yield self.title, self.header + "".join([n[0] for n in self.notes])
            return

        _accum = ""  # accumulated notes to be sent
        _sent = 0  # number of notes that have been returned so far

        for idx in range(len(self)):
            header = self.header if copy_header or _sent == 0 else ""
            note_size = len(header) + len(_accum)

            if len(self.notes[idx][0]) + len(header) > max_size:
                # this handles the case of when the header + a single note is bigger than max note size. also catches
                # cases where the note by itself is too long.
                raise RuntimeError(f"NOTE EXCEEDS MAX LENGTH OF {max_size} CHARACTERS: "
                                   f"'{self.title[:30]}', NOTE TEXT: '{self.notes[idx][0][:500]}'")

            if note_size + len(self.notes[idx][0]) > max_size:
                title = self.title if _sent == 0 else self.title + f" ({_sent})"

                yield title, header + _accum

                _accum = self.notes[idx][0]
                _sent += 1
            else:
                _accum += self.notes[idx][0]

        # since the note is added to _accum after yielding, we end up with extra notes in _accum that haven't been
        # sent yet. so we send them here.
        title = self.title if _sent == 0 else self.title + f" ({_sent})"
        header = self.header if copy_header or _sent == 0 else ""
        yield title, header + _accum


class BookList(dict):
    # todo: refactor: make a BookData class to store data of book title(s), highlight, length, count, etc
    #  BookData: fields for title, header, list of notes and sort keys or dict of {sort_key: note}?
    #            functions for formatting title, header, etc
    #  BookList: holds a dict of string titles of books with a BookData for each one.
    #            functions for add(title, note), split long dataset into multiple books, get base title
    #                of a split book, create headers when adding new notes, function to apply sent amount formatting
    def __init__(self):
        """
        this object is a dict of {book title: BookData object}
        """
        super().__init__()
        self.base_titles: Dict[str, str] = {}  # {full_title: base_title}

    def add_book(self, book: BookData):
        """
        adds a book to this BookList. If the book is already in this BookList, the old version is replaced.

        :param book: a BookData object to add to the book list
        :return: none
        """
        self[book.title] = book

    def add_note(self, title: str, note: str, sort_key: Any = 0) -> None:
        """
        adds a note to this book list. if the title already exists, the note is added to the appropriate BookData.
        otherwise, a new BookData will be created.

        :param title: title of the note being added
        :param note: contents of the note being added
        :param sort_key: used to sort the note within its file when sending to obsidian
        :return: none
        """
        if title in self:
            self[title].add_note(note, sort_key)
        else:
            b = BookData(title)
            b.add_note(note, sort_key)
            self[title] = b

    def update_title(self, old_title: str, new_title: str) -> None:
        """
        updates the title of the specified book if the book is in this BookList. If it's not in this BookList,
        raises an error.
        """
        if old_title in self:
            self[new_title] = self[old_title]
            del self[old_title]
        else:
            raise KeyError(f"Title {old_title} not found in BookList!")

    def update_header(self, book_title: str, header: str) -> None:
        """
        sets the specified book's header to the given value
        :return: none
        """
        if book_title in self:
            self[book_title].header = header
        else:
            raise KeyError(f"Title {book_title} not found in BookList!")

    def make_sendable_notes(self, max_size: int = -1, copy_header: bool = False) -> Iterable[Tuple[str, str]]:
        """
        :param max_size: maximum allowed size of a note (notes might be longer after headers are added)
        :param copy_header: if a single note is split into multiple, should the header be copied into each one,
        or should only the first note have a header?
        :return: yields an iterable of tuples containing (title, body) of notes to be sent to Obsidian.
        """
        for b in self:
            for n in self[b].make_sendable_notes(max_size, copy_header):
                yield n

    def apply_sent_amount_format(self, should_apply: Tuple[bool, bool, bool]) -> None:
        """
        applies formatting options {totalsent}, {booksent}, {highlightsent}.
        :return:
        """
        total_highlights = sum([len(self[title]) for title in self])
        for title in self:
            book_highlights = len(self[title])

            if should_apply[0]:  # title
                self.apply_sent_title(title, book_highlights, total_highlights)

            if should_apply[1]:  # body
                self.apply_sent_body(title, book_highlights, total_highlights)

            if should_apply[2]:  # header
                self.apply_sent_headers(title, book_highlights, total_highlights)

    def apply_sent_title(self, _title: str, _book_highlights: int, _total_highlights: int):
        """
        :param _title: title of the book whose title you want to apply sent amount formats to
        :param _book_highlights: Dict[title, int] that has the amount of highlights being sent to each book.
        :param _total_highlights: total number of highlights being sent
        :return: none
        """
        fmt = make_sent_format_dict(_total_highlights, _book_highlights, -1)
        new_title = format_single(fmt, _title)
        self[_title].title = new_title
        self[new_title] = self[_title]
        del self[_title]

    def apply_sent_body(self, _title: str, _book_highlights: int, _total_highlights: int):
        for h in range(len(self[_title])):
            # since BookData keeps its note list sorted, it's easy to know how many have been sent before this
            fmt = make_sent_format_dict(_total_highlights, _book_highlights, h + 1)
            self[_title].update_note(h, format_single(fmt, self[_title].notes[h][0]))

    def apply_sent_headers(self, _title: str, _book_highlights: int, _total_highlights: int):
        fmt = make_sent_format_dict(_total_highlights, _book_highlights, -1)
        self[_title].header = format_single(fmt, self[_title].header)


class HighlightSender:

    def __init__(self):
        # set defaults
        self.library_name = library_default_name
        self.vault_name = vault_default_name
        self.title_format = title_default_format
        self.body_format = body_default_format
        self.no_notes_format = no_notes_default_format
        self.header_format = header_default_format
        self.book_titles_authors = {}
        self.annotations_list = []
        self.max_file_size = -1  # -1 = unlimited
        self.copy_header = False
        self.sort_key = sort_key_default

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

    def set_header_format(self, header_format: str):
        """
        for each file that has highlights sent to it, the header will be sent before any highlights.
        note that this isn't once per file, if you send highlights to a file now and then again
        to the same file later, there will be two copies of the header.
        """
        self.header_format = header_format

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

    def set_max_file_size(self, max_file_size=-1, copy_header=False):
        """
        sets the maximum size of the body of files sent to obsidian, in text characters. If a file is too long,
        it will be split into smaller files that are under the max file size.

        :param max_file_size: max file size. If -1, file size is unlimited.
        :param copy_header: If True, the file's header will be copied to each file that the file is split into.
        :return: none
        """
        self.max_file_size = max_file_size
        self.copy_header = copy_header

    def set_sort_key(self, sort_key: str):
        """
        :param sort_key: key to use for sorting highlights. should be one of the formatting options, e.g. "timestamp",
        "location", "highlight", etc
        """
        # todo: verify that the sort key is valid
        self.sort_key = sort_key

    def should_apply_sent_formats(self) -> Tuple[bool, bool, bool]:
        """
        since formatting options for how many highlights were sent can't be applied until after the other formatting
        options are applied, they'll end up being applied to formatted strings instead of templates. depending on
        the content of those highlights, you could end up with very large strings. this function is a small performance
        boost: it'll only try to apply those formatting options if said formatting options are in templates.

        an alternative to this is to only format titles, and then count how many highlights will be sent to each
        note before you apply formatting to the body.

        :return: Tuple telling you if you need to apply formatting options for how many highlights were sent. Tuple is
        (title, body, header), where each item is True if that part needs formatting to be applied.
        """
        format_dict = make_sent_format_dict(0, 0, 0)
        formats = ("{" + k + "}" for k in format_dict.keys())
        title, body, header = False, False, False
        for f in formats:
            title = title or (f in self.title_format)
            body = body or (f in self.body_format) or (f in self.no_notes_format)
            header = header or (f in self.header_format)
        return title, body, header

    def make_obsidian_data(self, note_file, note_content):
        """
        limits length of note_file to 180 characters, allowing for an obsidian vault path of up to 80
        characters (Windows max path length is 260 characters).

        :param note_file: title of this note, including relative path
        :param note_content: body of this note
        :return: dictionary which includes vault name, note file/title, note contents.
        return value can be used as input for send_item_to_obsidian(). keys are "vault",
        "file", "content"
        """

        obsidian_data: Dict[str, str] = {
            "vault": self.vault_name,
            # use note_file[-4:] for the (1), (2), etc added to the end when there are a lot of highlights being sent
            "file": note_file if len(note_file) < 180 else note_file[:172] + "... " + note_file[-4:],
            "content": note_content,
            "append": "true",
        }

        return obsidian_data

    def format_sort_key(self, dat: Dict):
        """
        this function is necessary for handling things that can be used as sort keys, but
        don't work as the user would expect them to.

        :param dat: a value returned from make_format_dict
        :return: a sort key for sorting highlights
        """
        if self.sort_key == "location":
            # locations are something like "/int/int/int/int:int", but the ints aren't always the same length.
            # so normal string comparisons end up comparing "/" to numbers, which isn't what we want
            loc = dat[self.sort_key]
            locs = loc.split("/")  # first element is empty string since location starts with "/"
            locs, end = locs[1:-1], locs[-1]

            def get_num(x):
                # x[:x.find("[")] to catch locations with "[pXXX]" in them (XXX is a page number).
                # these locations seem to show up when there's more than one highlight in the same paragraph.
                y = x.find("[")
                if y == -1:
                    return int(x)
                else:
                    return int(x[:y])

            locs = [get_num(x) for x in locs]
            end = [get_num(x) for x in end.split(":")]
            # standardize list length to 8. i think amount of numbers in a location depends on how the book is
            # organized, but it's very rare to have that many nested sections, so this should work well enough
            # we use 8 because adding end increases length by 2, giving us a total length of 10
            ret = [locs[x] if x < len(locs) else 0 for x in range(8)] + end
            return tuple(ret)
        else:
            return dat[self.sort_key]

    def is_valid_highlight(self, _dat: Dict, condition: Callable[[Any], bool]):
        """
        :param condition: takes a highlight's json object and returns true if that highlight should be sent to obsidian.
        :param _dat: a dict with one calibre annotation's data
        :return: True if this is a valid highlight and should be sent, else False
        """
        _annot = _dat.get("annotation", {})
        if _annot.get("type") != "highlight":
            return False  # annotation must be a highlight, not a bookmark

        if _annot.get("removed"):
            return False  # don't try to send highlights that have been removed

        if not condition(_dat):  # or return condition(_dat)
            return False  # user-defined condition must be true for this highlight

        return True

    def process_highlight(self, _highlight, _headers: List[str]) -> Tuple[str, Tuple[str, Any], str]:
        """
        makes formatted data for a highlight.

        :param _highlight: a calibre annotation object
        :param _headers: list of titles that already have headers
        :return: (formatted_title, formatted_body, formatted_header)
        formatted_body is a tuple with (formatted_text, sort_key)
        formatted_header is None if a header is already present in _headers.
        """
        dat = make_format_dict(_highlight, self.library_name, self.book_titles_authors)
        formatted = format_data(dat, self.title_format, self.body_format, self.no_notes_format)

        # only make one header per title
        header = None if formatted[0] in _headers else format_single(dat, self.header_format)

        return formatted[0], (formatted[1], self.format_sort_key(dat)), header

    def send(self, condition: Callable[[Any], bool] = lambda x: True):
        """
        condition takes a highlight's json object and returns true if that highlight should be sent to obsidian.
        """

        highlights = filter(lambda x: self.is_valid_highlight(x, condition), self.annotations_list)
        headers = []  # formatted headers: dict[note_title:str, header:str]
        books = BookList()

        # make formatted titles, bodies, and headers
        for highlight in highlights:
            h = self.process_highlight(highlight, headers)
            books.add_note(h[0], h[1][0], h[1][1])
            if h[2] is not None:
                books.update_header(h[0], h[2])

        books.apply_sent_amount_format(self.should_apply_sent_formats())

        # todo: sometimes, if obsidian isn't already open, not all highlights get sent. probably need to send a single
        #  item then wait for obsidian to open
        for note in books.make_sendable_notes(self.max_file_size, self.copy_header):
            send_item_to_obsidian(self.make_obsidian_data(note[0], note[1]))

        return sum([len(b) for b in books.values()])
