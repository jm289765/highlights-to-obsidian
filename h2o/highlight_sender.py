import time
import webbrowser
from typing import Dict, List, Callable, Any
from urllib.parse import urlencode, quote
import datetime

# avoid importing anything from calibre or the highlights_to_obsidian plugin here


# might be better to move these into resource files
library_default_name = "Calibre Library"
vault_default_name = "My Vault"
title_default_format = "Books/{title} by {authors}"
body_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n{notes}\n\n---\n"
no_notes_default_format = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n---\n"
header_default_format = ""  # by default, no header
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

    pre_format = title.replace("{title}", remove_slashes(dat["title"]))
    return [remove_illegal_title_chars(pre_format.format(**dat)),
            body.format(**dat) if no_notes_body and len(dat["notes"]) > 0 else no_notes_body.format(**dat)]


def format_header(dat: Dict[str, str], header_format: str) -> str:
    """
    :param dat: output of make_format_dict. dict containing keys and values for string formatting.
    :param header_format:
    :return: string with formatted header
    """
    return header_format.format(**dat)


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

    # calibre's time format example: "2022-09-10T20:32:08.820Z"
    # the "Z" at the end means UTC time
    # "%Y-%m-%dT%H:%M:%S", take [:19] of the timestamp to remove milliseconds
    # better alternative might be dateutil.parser.parse
    h_time = datetime.datetime.strptime(annot["timestamp"][:19], "%Y-%m-%dT%H:%M:%S")
    h_local = h_time + h_time.astimezone(datetime.datetime.now().tzinfo).utcoffset()
    local = time.localtime()
    title_authors = book_titles_authors.get(int(data["book_id"]), {})  # dict with {"title": str, "authors": Tuple[str]}
    utc_offset = ("" if local.tm_gmtoff < 0 else "+") + str(local.tm_gmtoff // 3600) + ":00"

    # based on https://github.com/jplattel/obsidian-clipper
    format_options = {
        # if you add a key to this dict, also update the format_options local variable in config.py
        "title": title_authors.get("title", "Untitled"),  # title of book
        # todo: add "chapter" option
        "authors": title_authors.get("authors", ("Unknown",)),  # authors of book
        "highlight": annot["highlighted_text"],  # highlighted text
        "blockquote": format_blockquote(annot["highlighted_text"]),  # block-quoted highlight
        "notes": annot["notes"] if "notes" in annot else "",  # user's notes on this highlight
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
        "utcoffset": utc_offset,
        "timeoffset": utc_offset,  # for backwards compatibility
        "day": str(h_time.day),
        "localday": str(h_local.day),
        "month": str(h_time.month),
        "localmonth": str(h_local.month),
        "year": str(h_time.year),
        "localyear": str(h_local.year),
        "url": url_format.format(**url_args),  # calibre:// url to open ebook viewer to this highlight
        "location": url_args["location"],  # epub cfi location of this highlight
        "timestamp": h_time.timestamp(),  # Unix timestamp of highlight time. uses UTC.
        "bookid": data["book_id"],
        "uuid": annot["uuid"],  # highlight's ID in calibre
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
        self.header_format = header_default_format
        self.book_titles_authors = {}
        self.annotations_list = []
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

    def set_sort_key(self, sort_key: str):
        """
        :param sort_key: key to use for sorting highlights. should be one of the formatting options, e.g. "timestamp",
        "location", "highlight", etc
        """
        # todo: verify that the sort key is valid
        self.sort_key = sort_key

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

        highlights = filter(lambda a: a.get("annotation", {}).get("type") == "highlight",
                            self.annotations_list)  # annotations["annotations"])
        dats = []  # List[List[obsidian_data, sort_key]]
        headers = {}  # dict[note_title:str, header:str]

        for highlight in highlights:
            if highlight["annotation"].get("removed", False):
                continue  # don't try to send highlights that have been removed

            if not condition(highlight):
                continue

            dat = make_format_dict(highlight, self.library_name, self.book_titles_authors)
            formatted = format_data(dat, self.title_format, self.body_format, self.no_notes_format)

            if formatted[0] not in headers:
                headers[formatted[0]] = format_header(dat, self.header_format)

            dats.append([formatted, self.format_sort_key(dat)])

        def merge_highlights(data):
            """
            returns a dictionary with formatted highlights merged into a single string for each
            unique formatted note title found in dats.

            This limits the length of merged note contents to 20000 characters. If the length exceeds this, extra
            highlights will use a different title, e.g. "The Book", "The Book (1)", etc

            for reference, format_data() output is a list of [title, body]

            :param data: List[List[format_data() output, sort_key]]
            :return: list of obsidian_data objects, where each unique title from the input is merged into a
            single, sorted item in the output.
            """
            # this function has too many nested index lookups, it could use some simplification

            books = {}  # dict[str, list[list[obsidian_data object, sort_key]]
            lengths = {}
            # make list of highlights for each note title
            for d in data:
                format_dat = d[0]  # list[title, body]
                body_and_sort = [format_dat[1], d[1]]  # [note body, sort key]
                base_title = format_dat[0]

                # limit each merged highlight to 20000 chars. it could be higher, but we need room for url encoding.
                #
                # This is necessary because some operating systems have a limit to how long a uri can be. or maybe the
                # problem is some detail about how webbrowser.open() is implemented. on my windows 11 laptop, calling
                # webbrowser.open("obsidian://" + "a" * 32699) works, but "a" * 32700 will open microsoft edge instead,
                # and if the number reaches 32757 it gives an error.
                note_title, l = base_title, lengths.get(base_title, False)
                if l:  # limit size of a note's content to 20 kb.
                    splits = l // 20000
                    if splits > 0:
                        note_title = base_title + f" ({splits})"

                if note_title in books:
                    books[note_title].append(body_and_sort)
                else:
                    books[note_title] = [body_and_sort]

                if base_title in lengths:
                    lengths[base_title] += len(body_and_sort[0])
                else:
                    lengths[base_title] = len(body_and_sort[0])

            # now, books contains lists of unsorted [note body, sort key] objects
            ret = []

            for key in books:
                # sort each book's highlights and then merge them into a single string
                books[key].sort(key=lambda body_sort: body_sort[1])
                # header is only included in first of a series of same-book files
                # (this happens when there's too much text to send to a single file at once)
                text = headers.get(key, "") + "".join([a[0] for a in books[key]])
                ret.append(self.make_obsidian_data(key, text))

            return ret

        # todo: sometimes, if obsidian isn't already open, not all highlights get sent
        merged = merge_highlights(dats)
        for obsidian_dat in merged:
            send_item_to_obsidian(obsidian_dat)

        return len(dats)
