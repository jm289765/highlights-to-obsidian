import time
import webbrowser
from typing import Dict, List
from urllib.parse import urlencode, quote
import datetime
# avoid importing anything from the calibre plugin here


# relative or absolute path to annotations file exported from calibre
# to use this program, set this variable and then run it
calibre_annotations_path = r"C:\Users\Admin\Documents\Github\highlights-to-obsidian\annotations.calibre_annotation_collection"

# format strings for the title and contents of the note being sent to obsidian
# for a full list of formatting options, see the variable format_options in the function make_format_dict
note_title = "Books/Book {title}"
note_body = "\n[Highlighted]({url}) on {date} at {time} UTC {timeoffset}:\n{blockquote}\n\n{notes}\n\n---\n"


def send_item_to_obsidian(obsidian_data: Dict[str, str]) -> None:
    encoded_data = urlencode(obsidian_data, quote_via=quote)
    uri = "obsidian://new?" + encoded_data
    webbrowser.open(uri)


def format_data(title: str, body: str, dat: Dict[str, str]) -> List[str]:
    """
    apply string.format() to title and body with data values from dat. Also removes slashes from title.

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
    return [remove_illegal_title_chars(pre_format.format(**dat)), body.format(**dat)]


def make_format_dict(data: Dict[str, str]) -> Dict[str, str]:  # takes calibre json highlight data as input
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
    url_format = "calibre://view-book/{library}/{book_id}/{book_format}?open_at=epubcfi({location})"
    url_args = {
        "library": "Calibre Library".replace(" ", "_"),  # todo: don't hardcode the library name
        "book_id": data["book_id"],
        "book_format": data["format"],
        "location": data["start_cfi"],
    }

    local = time.localtime()

    format_options = {
        "title": data["book_id"],  # title of book
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
        "uuid": data["uuid"],  # highlight's ID in calibre
    }

    return format_options


def send_highlights(title_format: str = note_title, body_format: str = note_body, last_send_time: time.struct_time = None):
    """
    sends highlights to obsidian. currently uses the annotations.calibre_annotation_collection
    file to get highlight data.

    if last_send_time isn't None, this will exclude any highlights that were made before last_send_time
    """
    # encoding has to be 'utf-8-sig' because calibre annotation files use BOM
    file = open(calibre_annotations_path, encoding='utf-8-sig')

    from json import load
    annotations = load(file, parse_int=str, parse_float=str, parse_constant=str)

    # todo: find a way to exclude highlights that have already been sent to obsidian.
    # will likely use uuids or timestamps: make a list of uuids that have already been
    # sent and then filter out uuids on that list, or filter out highlights with times
    # that were before the most recent run of highlights-to-obsidian
    highlights = filter(lambda a: a["type"] == "highlight", annotations["annotations"])

    for highlight in highlights:
        dat = make_format_dict(highlight)
        # todo: filter out highlights before last_send_time if last_send_time is not None
        formatted = format_data(title_format, body_format, dat)

        obsidian_data: Dict[str, str] = {
            "vault": "Test",
            "file": formatted[0],
            "content": formatted[1] + str(last_send_time),
            "append": "true",
        }

        send_item_to_obsidian(obsidian_data)


if __name__ == "__main__":
    send_highlights()
