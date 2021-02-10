from ago import human
from datetime import datetime
from webbrowser import open as webopen

def sec_to_mins(seconds):
    a = str(round((seconds % 3600)//60))
    b = str(round((seconds % 3600) % 60))
    d = f"{a}m {b}s"
    return d

def agoConv(datetimeStr):
    if datetimeStr:
        _ago = human(datetime.strptime(datetimeStr, '%Y-%m-%d %H:%M:%S.%f'),
        abbreviate=True)
        if 's' in _ago[:3]:
            return 'now' 
        else:
            return _ago
    else:
        return 'Pic a list'

def open_link(link):
    webopen(link)
    return True