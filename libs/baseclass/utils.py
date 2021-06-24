from ago import human
from datetime import datetime
from webbrowser import open as webopen
from kivymd.toast import toast
from kivy.core.clipboard import Clipboard


def sec_to_mins(seconds):
    a = str(round((seconds % 3600)//60))
    b = str(round((seconds % 3600) % 60))
    d = f"{a}m {b}s"
    return d


def agoConv(datetimeStr):
    if datetimeStr:
        _ago = human(
            datetime.strptime(datetimeStr, '%Y-%m-%d %H:%M:%S.%f'),
            abbreviate=True)

        if 'ms' in _ago.split(',')[0]:
            return 'Now'
        elif "s" in _ago.split(',')[0]:
            return _ago.split(',')[0] 
        elif "y" or "d" or "h" or "m" in _ago.split(',')[0]:
            if ('ms' or 'um') == _ago.split(',')[1][-6:-4]:
                return _ago.split(',')[0]
            return _ago.replace('ago', '')
        # else:
        #     return _ago
    else:
        return ''


def open_link(link):
    webopen(link)
    return True


def copy_proxyip(text):
    toast(f"Copied: {text}")
    Clipboard.copy(text)
