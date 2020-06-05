import os

from kivy.uix.modalview import ModalView

from kivy.utils import get_color_from_hex, get_hex_from_color

from kivymd.color_definitions import palette, colors
from kivymd.theming import ThemableBehavior
import re
from kivymd.toast import toast
import sqlite3
from datetime import datetime
# from main import ProxySpeedTestApp

conn = sqlite3.connect('database.db')
c = conn.cursor()


class KitchenSinkBaseDialog(ThemableBehavior, ModalView):
    pass


class KitchenSinkDialogDev(KitchenSinkBaseDialog):
    pass

class PSTDialogInput(KitchenSinkBaseDialog):
    def __init__(self, **kwargs):
        super(PSTDialogInput, self).__init__(**kwargs)
        # self.filename = 'proxys.txt'

        # if os.path.exists(self.filename):
        #     with open(self.filename, 'r', encoding="utf-8") as r:
        #         self.ids.query.text = r.read()
        # with conn:
        #     c.execute("SELECT proxysInx FROM 'configs'")
        #     self.selLId = c.fetchone()[0]

        #     c.execute("SELECT ip FROM 'proxys' WHERE time=?", [self.selLId])
        #     getips = c.fetchall()
        
        # self.proxys = [ip[0] for ip in getips]
        # currentSavedList = ""
        # for line in self.proxys:
        #     currentSavedList += line+'\n'
        # self.ids.query.text = currentSavedList

        self.piced_pro = None
    

    def inputedproxysSave(self):

        proxys = re.findall(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}[\s:\t][0-9]{1,5}",
        self.ids.query.text)
        for line in range(len(proxys)):
            proxys[line] = re.sub(r'[\s]', ':', proxys[line])
        if not proxys:
            toast(f"Save error!\nNo ip:port found!")
            self.ids.query.text = ""
            return False
        currentSave = ""
        for line in proxys:
            currentSave += line+'\n'
        
        IndexTime = datetime.now()
        # protocol = 'socks4'
        with conn:
            for l in proxys:
                if not l:continue
                try:
                    c.execute('INSERT INTO proxys (time, ip, protocol) VALUES (?, ?, ?)', (IndexTime, l, self.piced_pro))
                except sqlite3.OperationalError as e:
                    print(e)
            c.execute("UPDATE 'configs' SET proxysInx=?", [IndexTime])
            c.execute("INSERT INTO proxysInx VALUES (?)", [IndexTime])
        
            
        self.ids.query.text = currentSave
        
        
        toast(f"Saved successful!\nInputed {len(proxys)}!")


class MirrorDialogInput(KitchenSinkBaseDialog):
    def __init__(self,mainClass, **kwargs):
        super().__init__(**kwargs)
        # self.filename = 'proxys.txt'
        self.mainClass = mainClass
        # if os.path.exists(self.filename):
        #     with open(self.filename, 'r', encoding="utf-8") as r:
        #         self.ids.query.text = r.read()
        with conn:
            c.execute("SELECT * FROM 'mirrors'")
            self.mirrors = c.fetchall()
        self.showsInBox = ""
        for m in self.mirrors:
            self.showsInBox += m[0]+'\n'
        self.ids.queryMirror.text = self.showsInBox


    
    def inputedMirrorSave(self):
        
        if self.showsInBox != self.ids.queryMirror.text:
            with conn:
                c.execute("DROP TABLE 'mirrors'")
                c.execute("create table mirrors (mirror text)")
                for line in self.ids.queryMirror.text.split('\n'):  
                    if not line == '':
                        # print(line)
                        c.execute("INSERT INTO mirrors VALUES (?)", [line.strip()])
                c.execute("UPDATE 'configs' SET miInx=0")
                self.mainClass.mirrorPic()
            toast(f"Saved!")
        else:
            toast('No new updated!')
        


class KitchenSinkDialogLicense(KitchenSinkBaseDialog):
    def on_open(self):
        with open(
            os.path.join(os.environ["KITCHEN_SINK_ROOT"], "LICENSE"),
            encoding="utf-8",
        ) as license:
            self.ids.text_label.text = license.read().format(
                COLOR=get_hex_from_color(self.theme_cls.primary_color)
            )


class KitchenSinkDialogChangeTheme(KitchenSinkBaseDialog):
    def set_list_colors_themes(self):
        for name_theme in palette:
            self.ids.rv.data.append(
                {
                    "viewclass": "KitchenSinkOneLineLeftWidgetItem",
                    "color": get_color_from_hex(colors[name_theme]["500"]),
                    "text": name_theme,
                }
            )
