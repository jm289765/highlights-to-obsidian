import webbrowser
from urllib.parse import urlencode, quote_plus, quote
import datetime
import time



data = {
    "vault":"Test", 
    "file": "abc\\" + str(time.time()), #datetime.date().today, 
    "content": "This is a test", 
    "append": "true"
    }

def send_to_obsidian(data):
    encoded_data = urlencode(data, quote_via=quote)
    uri = "obsidian://new?" + encoded_data
    print(uri)
    print(quote_plus("abc def/hij"))

    webbrowser.open(uri)
