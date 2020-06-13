import os

from kivy.uix.modalview import ModalView

from kivy.utils import get_color_from_hex, get_hex_from_color

from kivymd.color_definitions import palette, colors
from kivymd.theming import ThemableBehavior
import re
from kivymd.toast import toast
import sqlite3
from datetime import datetime
from hurry.filesize import size
# from main import ProxySpeedTestApp
databaseFilename = 'database.db'

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
        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            for l in proxys:
                if not l:continue
                try:
                    c.execute('INSERT INTO proxys (time, ip, protocol) VALUES (?, ?, ?)', (IndexTime, l, self.piced_pro))
                except sqlite3.OperationalError as e:
                    print(e)
            c.execute("UPDATE 'configs' SET proxysInx=?", [IndexTime])
            c.execute("INSERT INTO proxysInx VALUES (?)", [IndexTime])
        conn.commit()
        conn.close()
        
        self.ids.query.text = currentSave
        
        toast(f"Saved successful!\nInputed {len(proxys)}!")
        self.dismiss()


class MirrorDialogInput(KitchenSinkBaseDialog):
    def __init__(self,mainClass, **kwargs):
        super().__init__(**kwargs)
        # self.filename = 'proxys.txt'
        self.mainClass = mainClass
        # if os.path.exists(self.filename):
        #     with open(self.filename, 'r', encoding="utf-8") as r:
        #         self.ids.query.text = r.read()

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("SELECT * FROM 'mirrors'")
            self.mirrors = c.fetchall()
        conn.commit()
        conn.close()

        self.showsInBox = ""
        for m in self.mirrors:
            self.showsInBox += m[0]+'\n'
        self.ids.queryMirror.text = self.showsInBox


    
    def inputedMirrorSave(self):
        
        if self.showsInBox != self.ids.queryMirror.text:
            conn = sqlite3.connect(databaseFilename)
            c = conn.cursor()
            with conn:
                c.execute("DROP TABLE 'mirrors'")
                c.execute("create table mirrors (mirror text)")
                for line in self.ids.queryMirror.text.split('\n'):  
                    if not line == '':
                        # print(line)
                        c.execute("INSERT INTO mirrors VALUES (?)", [line.strip()])
                c.execute("UPDATE 'configs' SET miInx=0")
                self.mainClass.mirrorPic()
            conn.commit()
            conn.close()
            toast(f"Saved!")
        else:
            toast('No new updated!')
        

class TimeoutSet(KitchenSinkBaseDialog):
    def __init__(self,updateText, **kwargs):
        super().__init__(**kwargs)

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("SELECT timeoutD FROM 'configs'")
            self.timeoutD = c.fetchone()[0]
        conn.commit()
        conn.close()

        self.updateText = updateText
        self.ids.queryTimeout.text = str(self.timeoutD)


    
    def inputedTimeoutSave(self):
        setTimeout = int(self.ids.queryTimeout.text)
        if self.timeoutD != setTimeout:
            
            conn = sqlite3.connect(databaseFilename)
            c = conn.cursor()
            with conn:
                c.execute("UPDATE 'configs' SET timeoutD=?", [setTimeout])
            conn.commit()
            conn.close()
            self.updateText.text = f"Timeout : {setTimeout} seconds"
            toast(f"Saved! {setTimeout} seconds")
            self.dismiss()
        else:
            toast('No new updated!')

class FilesizeSet(KitchenSinkBaseDialog):
    def __init__(self,updateText, **kwargs):
        super().__init__(**kwargs)

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("SELECT fileSize FROM 'configs'")
            self.filesize = c.fetchone()[0]
        conn.commit()
        conn.close()

        self.updateText = updateText
        self.ids.queryFilesize.text = str(self.filesize)


    
    def inputedFilesizeSave(self):
        setFilesize = int(self.ids.queryFilesize.text)
        if self.filesize != setFilesize:

            conn = sqlite3.connect(databaseFilename)
            c = conn.cursor()
            with conn:
                c.execute("UPDATE 'configs' SET fileSize=?", [setFilesize])
            conn.commit()
            conn.close()
            
            self.updateText.text = f"Filesize : {size(setFilesize)}"
            toast(f"Saved! {size(setFilesize)}")
            self.dismiss()
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
