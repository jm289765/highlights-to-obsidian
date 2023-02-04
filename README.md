Highlights to Obsidian is a plugin for Calibre ebook manager that formats and sends highlights to Obsidian.md markdown editor. This plugin's calibre forum post can be found [here](https://www.mobileread.com/forums/showthread.php?t=351283).

After installing, go to Preferences -> Toolbars & menus -> The main toolbar. The highlights to obsidian menu button is listed as H2O.

---

You can update the formatting of highlights sent to Obsidian in this plugin's config menu at Preferences -> Plugins -> User interface action -> Highlights to Obsidian.

If you don't want your first time sending new highlights to Obsidian to send all highlights, update the last send time in the config.

Sometimes, if you send highlights while your obsidian vault is closed, not all highlights will be sent. If this happens, you can use the "Resend Previously Sent Highlights" function.

You can set keyboard shortcuts in Preferences -> Shortcuts -> H2O. Some available keyboard shortcuts include CTRL+S, CTRL+E, CTRL+G, CTRL+H, CTRL+J, and CTRL+K.

---

Available formatting options are as follows:

- {title}: Title of the book the highlight is in.
- {authors}: Authors of the book the highlight is in.
- {highlight}: The highlighted text.
- {blockquote}: The highlighted text, formatted as a blockquote. an arrow and a space "> " are added to the beginning of each line.
- {notes}: The user's notes on this highlight, if any notes exist. There is a config option that allows you to set different formatting depending on whether a highlight includes notes.
- {date}: Date the highlight was made, formatted as YYYY-MM-DD
- {time}: Time the highlight was made, formatted as HH:MM:SS
- {datetime}: Date and time highlight was made, formatted as YYYY-MM-DD HH:MM:SS
- {localdate}, {localtime}, {localdatetime}
- {timezone}: The timezone that your computer is currently set to. Note that this may not always match the timezone the highlight was made in. This uses the full name, as in "Coordinated Universal Time", instead of the abbreviation, as in "UTC".
- {utcoffset} or {timeoffset}: The UTC offset of your computer's current time zone. For example, UTC time gives +0:00. EST time can be -4:00 or -5:00, depending on daylight savings time.
- {day}: Day of the month the highlight was made, as in 3 or 17
- {month}: Month the highlight was made, as in 4 for April or 10 for October
- {year}: Full year the highlight was made, as in 2022
- {localday}, {localmonth}, {localyear}
- {url}: A [calibre:// url](https://manual.calibre-ebook.com/url_scheme.html) to open the ebook viewer to this highlight. Note that this may not work if your library's name contains unsafe URL characters. Numbers, letters, spaces, underscores, and hyphens are all safe.
- {location}: The highlight's EPUB CFI location in the book. For example, "/2/8/6/5:192". As a sort key, this will order highlights by their position in the book.
- {timestamp}: The highlight's Unix timestamp. This is the default sort key used to determine what order to send highlights in.
- {bookid}: The book's ID in calibre. 
- {uuid}: The highlight's unique ID in calibre. For example, "TlNlh8_I5VGKUtqdfbOxDw".

For an example of how to use these, see the default format settings in the plugin's config.

---

Formatting options based on the [Obsidian Clipper](https://github.com/jplattel/obsidian-clipper) Chrome extension.
