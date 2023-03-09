import time
import webbrowser
from typing import Dict, List, Callable, Any, Tuple
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
        "day": str(h_time.day),
        "localday": str(h_local.day),
        "month": str(h_time.month),
        "localmonth": str(h_local.month),
        "year": str(h_time.year),
        "localyear": str(h_local.year),
        "hour": str(h_time.hour),
        "localhour": str(h_local.hour),
        "minute": str(h_time.minute),
        "localminute": str(h_local.minute),
        "second": str(h_time.second),
        "localsecond": str(h_local.second),
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

    def send(self, condition: Callable[[Any], bool] = lambda x: True):
        """
        condition takes a highlight's json object and returns true if that highlight should be sent to obsidian.
        """

        # todo: a lot of the lists used here and in related functions could probably be replaced with tuples

        def is_valid_highlight(_dat: Dict):
            """
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

        def format_add_highlight(_highlight, _dats, _headers):
            """
            makes a formatted highlight from an annotation data object, then updates _dats and _headers.

            :param _highlight: a calibre annotation object
            :param _dats: list to be updated in-place. a list [format_data() output, sort_key] will be appended.
            :param _headers: dict to be updated in-place. if we come across a title that's not in the dict,
            a formatted header will be made for that title.
            :return: none
            """
            dat = make_format_dict(_highlight, self.library_name, self.book_titles_authors)
            formatted = format_data(dat, self.title_format, self.body_format, self.no_notes_format)

            if formatted[0] not in _headers:  # only make one header per title
                _headers[formatted[0]] = format_single(dat, self.header_format)

            _dats.append([formatted, self.format_sort_key(dat)])

        def merge_highlights(data, _headers):
            """
            merges formatted highlights into a single string for each unique note title found in dats.

            This limits the length of merged note contents to 20000 characters. If the length exceeds this, extra
            highlights will use a different title, e.g. "The Book", "The Book (1)", etc

            for reference, format_data() output is a list of [title, body]

            :param data: list of all formatted highlights: List[List[format_data() output, sort_key]]
            :param _headers: formatted headers: dict[note_title:str, header:str]. sent amount formatting will be applied
            in-place.
            :return: list of obsidian_data objects, where each unique title from the input is merged into a
            single, sorted item in the output.
            """

            def add_data_item(_dat, _books, _lengths, _counts):
                """
                :param _dat: data item: [[title, body], sort_key]
                :param _books: dict that will be updated in-place. will have a format_data() output and sort key
                added to a note title. like _books["title"].append([formatted_body, sort_key]). automatically handles
                cases where "title" is not in _books.
                :param _lengths: dict that may be updated in-place, used for tracking cumulative length of highlights
                :param _counts: dict of {title, int} for how many highlights each book has. can't be done by taking
                length of _books[title] because _books splits large amounts of highlights for a single title into
                more than one title with a smaller amount of highlights each.
                :return: none
                """
                format_dat = _dat[0]  # list[title, body]
                body_and_sort = [format_dat[1], _dat[1]]  # [note body, sort key]
                base_title = format_dat[0]
                note_length, note_title = len(body_and_sort[0]), base_title

                def add_item_to_note(note, item):
                    if note in _books:
                        _books[note].append(item)
                    else:
                        _books[note] = [item]

                def add_length_to_note(note, length):
                    lngth = _lengths.get(note, 0)
                    cts = _counts.get(note, 0)
                    if self.max_file_size > -1:
                        note_count = lngth // self.max_file_size
                        next_max = self.max_file_size * (note_count + 1)
                        if length + lngth > next_max:
                            # file will be too big if this highlight is added, so we skip to the start of the next file
                            # checking for length > max_file_size is done before this function is called
                            lngth = next_max

                    _lengths[note] = lngth + length
                    _counts[note] = cts + 1

                if -1 < self.max_file_size < note_length:  # note is too big, no file can hold it
                    return

                # do this before add_item_to_note so we can figure out what number to append to note title
                add_length_to_note(base_title, note_length)

                # limit the file size of notes
                if self.max_file_size > -1:
                    l = _lengths.get(base_title, 0)
                    splits = l // self.max_file_size
                    if splits > 0:
                        note_title = base_title + f" ({splits})"

                add_item_to_note(note_title, body_and_sort)

            # todo: refactor: put base_title in a data object with the modified title instead of calculating it here
            def get_base_title(_title: str, _valid_titles: List[str]) -> str:
                """if this is part of a split note, e.g. "title (1)" or "title (2)", remove the " (x)" """
                # todo: change the data format for split note titles, so that you can simplify this
                _ret = _title
                # space, parentheses, number, parentheses, end of string
                __match = regex.search(" \((\d+)\)$", _title)
                if __match:
                    base = _title[:_title.rfind(" ")]
                    if base in _valid_titles:
                        _ret = base
                return _ret

            def apply_sent_amount_format(_books: Dict[str, List], _headers: Dict[str, str],
                                         book_highlights: Dict[str, int], total_highlights: int):
                """
                :param _books: formatted highlights being sent to each book (will be updated in-place):
                dict[title:str, list[list[formatted_body, sort_key]]
                :param _headers: formatted headers: dict[note_title:str, header:str]. sent amount formatting will be
                 applied in-place.
                :param book_highlights: Dict[title, int] that has the amount of highlights being sent to each book.
                :param total_highlights: total number of highlights being sent
                :return: none
                """

                def apply_sent_title(_books, _headers, _book_highlights:Dict[str,int], _total_highlights:int):
                    # use list(_books.keys()) so that we don't get an error by changing dict keys during iteration
                    _b = list(_books.keys())
                    for t in _b:  # t: book title (str)

                        base_title = get_base_title(t, _b)

                        fmt = make_sent_format_dict(_total_highlights, _book_highlights[base_title], -1)
                        new_title = format_single(fmt, t)
                        _books[new_title] = _books[t]
                        del _books[t]
                        if t in _headers:
                            _headers[new_title] = _headers[t]
                            del _headers[t]
                        if t in _book_highlights:
                            _book_highlights[new_title] = _book_highlights[t]

                def apply_sent_body(_books, _book_highlights:Dict[str,int], _total_highlights:int):
                    valid_titles = list(_books.keys())
                    for t in _books:  # t: book title (str)
                        def count_highlights_before(_title, _base, __books) -> int:
                            """
                            if a highlight has " (x)" at the end, count the highlights being sent to previous notes

                            :param _title: title of the note these highlights are being sent to
                            :param _base: base title for this title
                            :param __books: dict[title, list[highlights]]
                            :return: number of highlights in notes with same base title but a lower x in their " (x)"
                            """
                            _ret = 0
                            _b, _t = len(_base), len(_title)
                            if _b != _t:
                                title_number = int(_title[_b + 2:-1])  # t is base title + " (num)"
                                _ret = len(__books[_base])
                                for x in range(1, title_number):
                                    _ret += len(__books[_base + f" ({x})"])

                            return _ret

                        base_title = get_base_title(t, valid_titles)
                        highlights_before = count_highlights_before(t, base_title, _books)

                        for h in range(len(_books[t])):  # _books[h]: [formatted body, sort_key]
                            fmt = make_sent_format_dict(_total_highlights, _book_highlights[base_title],
                                                        highlights_before + h + 1)
                            _books[t][h][0] = format_single(fmt, _books[t][h][0])

                def apply_sent_headers(_headers, _book_highlights:Dict[str,int], _total_highlights:int):
                    for h in _headers:  # h: book title (str)
                        fmt = make_sent_format_dict(_total_highlights, _book_highlights[h], -1)
                        _headers[h] = format_single(fmt, _headers[h])

                # todo: _books and _headers being updated in-place is a source of bugs. change it

                should_apply = self.should_apply_sent_formats()

                if should_apply[0]:  # title
                    apply_sent_title(_books, _headers, book_highlights, total_highlights)

                if should_apply[1]:  # body
                    apply_sent_body(_books, book_highlights, total_highlights)

                if should_apply[2]:  # header
                    apply_sent_headers(_headers, book_highlights, total_highlights)

            # todo: refactor: make a class to store data of book title, highlight, length, count, etc
            books = {}  # dict[title:str, list[list[obsidian_data object:Dict, sort_key]]
            lengths = {}  # amount of characters per book. dict[book title:str, int]
            counts = {}  # amount of highlights per book. dict[book title:str, int]

            # make list of highlights for each note title
            for d in data:
                add_data_item(d, books, lengths, counts)

            # sort books here to that apply_sent_amount_format gives accurate position of highlight in note
            for key in books:
                books[key].sort(key=lambda body_sort: body_sort[1])

            apply_sent_amount_format(books, headers, counts, len(data))

            # now, `books` contains lists of unsorted [note body, sort key] objects
            ret = []

            # merge each book's highlights into a single string. also add headers.
            header_keys = list(headers.keys())
            for key in books:
                # header is only included in first of a series of same-book files
                # (this happens when there's too much text to send to a single file at once)
                if self.copy_header:
                    header = headers.get(get_base_title(key, header_keys), "")
                else:
                    header = headers.get(key, "")
                text = header + "".join([a[0] for a in books[key]])
                ret.append(self.make_obsidian_data(key, text))

            return ret

        highlights = filter(is_valid_highlight, self.annotations_list)  # annotations["annotations"])
        dats = []  # formatted titles and bodies: List[List[format_data() output, sort_key]]
        headers = {}  # formatted headers: dict[note_title:str, header:str]

        # make formatted titles, bodies, and headers
        for highlight in highlights:
            format_add_highlight(highlight, dats, headers)

        # todo: sometimes, if obsidian isn't already open, not all highlights get sent
        merged = merge_highlights(dats, headers)
        for obsidian_dat in merged:
            send_item_to_obsidian(obsidian_dat)

        return len(dats)
