
# Highlights to Obsidian

Highlights to Obsidian is a plugin for the calibre ebook manager that formats and sends highlights to Obsidian.md markdown editor. This plugin [can be found](https://www.mobileread.com/forums/showthread.php?t=351283) on the calibre forum.

After installing, go to Preferences -> Toolbars & menus -> The main toolbar. The Highlights to Obsidian menu button is listed as H2O.

1. [[#Useful Info]]
2. [[#Formatting Options]]
3. [[#Misc]]

## Useful Info

- You can update the formatting of highlights sent to Obsidian in the config menu at Preferences -> Plugins -> User interface action -> Highlights to Obsidian.

- If you don't want the first time sending new highlights to send all of your highlights, you can update the last send time in the config.

- In the formatting config menu, the 'title' is the title of the note that a highlight will be sent to. The 'body' is the text that will be sent to that note for each highlight. The 'header' will be sent to each note exactly once when you send highlights.

- In a note's title, you can include slashes "/" to specify what folder the note should be in.

- Sometimes, if you send highlights while your Obsidian vault is closed, not all highlights will be sent. If this happens, you can use the "Resend Previously Sent Highlights" function.

- You can set keyboard shortcuts in Preferences -> Shortcuts -> H2O.

- Due to URI length limits, H2O can only send a few thousand words to a single note at once. Extra text will be sent to different notes with increasing numbers added to the end of the title.

## Formatting Options

For an example of how to use these, see the default format settings in the plugin's config menu.

**Book:**
- {title}: Title of the book the highlight is in.
- {authors}: Authors of the book the highlight is in.
- {bookid}: The book's ID in calibre. 

**Highlight:**
- {highlight}: The highlighted text.
- {blockquote}: The highlighted text, formatted as a blockquote. an arrow and a space "> " are added to the beginning of each line.
- {notes}: The user's notes on this highlight, if any notes exist. There is a config option that allows you to set different formatting depending on whether a highlight includes notes.
- {url}: A [calibre:// url](https://manual.calibre-ebook.com/url_scheme.html) to open the ebook viewer to this highlight. Note that this may not work if your library's name contains unsafe URL characters. Numbers, letters, spaces, underscores, and hyphens are all safe.
- {location}: The highlight's EPUB CFI location in the book. For example, "/2/8/6/5:192". As a sort key, this will order highlights by their position in the book.
- {timestamp}: The highlight's Unix timestamp. As a sort key, this will order highlights by when they were made.
- {uuid}: The highlight's unique ID in calibre. For example, "TlNlh8_I5VGKUtqdfbOxDw".

**Time:**
- {date}: Date the highlight was made, formatted as YYYY-MM-DD.
- {time}: Time the highlight was made, formatted as HH:MM:SS.
- {datetime}: Date and time highlight was made, formatted as YYYY-MM-DD HH:MM:SS.
- {day}: Day of the month the highlight was made, as in 3 or 17.
- {month}: Month the highlight was made, as in 4 for April or 10 for October.
- {year}: Full year the highlight was made, as in 2022.
- {hour}: Hour the highlight was made, based on a 24-hour (not 12-hour) system.
- {minute}: Minute the highlight was made.
- {second}: Second the highlight was made.
- {utcnow}: current time, formatted same as {datetime}.
- {datenow}: Current date, formatted same as {date}.
- {timenow}: Current time, formatted same as {time}.
- {timezone}: The timezone that your computer is currently set to. Note that this may not always match the timezone the highlight was made in. Also note that this might use the full name "Coordinated Universal Time" instead of the abbreviation "UTC".
- {utcoffset}: The UTC offset of your computer's current time zone. For example, UTC time gives +0:00. EST time can be -4:00 or -5:00, depending on daylight savings time.
- All time options use UTC by default. To use your computer's local time zone instead, add "local" to the beginning: {localdate}, {localtime}, {localdatetime}, {localday}, {localmonth}, {localyear}, {localhour}, {localminute}, {localsecond}, {localnow}, {localdatenow}, {localtimenow}.

**Highlights to Obsidian:**
- {totalsent}: The total number of highlights being sent.
- {booksent}: The total number of highlights being sent to this Obsidian note.
- {highlightsent}: This highlight's position in the highlights being sent to this note. For example, "{highlightsent} out of {booksent}" might result in "3 out of 5".

## Misc

This plugin is loosely based on the [Obsidian Clipper](https://github.com/jplattel/obsidian-clipper) Chrome extension.

The file `h2o-index.txt` is for the [plugin index page](https://www.mobileread.com/forums/showthread.php?t=118764) on the calibre forum.
