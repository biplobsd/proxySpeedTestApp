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
from database import MyDb
from kivy.base import EventLoop

dbRW = MyDb()

class KitchenSinkBaseDialog(ThemableBehavior, ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        # self.auto_dismiss = False

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            # print("Back button clicked!")
            self.dismiss()
        return True 


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
        dbRW.createProxysList(proxys, self.piced_pro, IndexTime)

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

        
        self.mirrors = dbRW.getAllMirrors()

        self.showsInBox = ""
        for m in self.mirrors:
            self.showsInBox += m[0]+'\n'
        self.ids.queryMirror.text = self.showsInBox


    
    def inputedMirrorSave(self):
        
        if self.showsInBox != self.ids.queryMirror.text:

            dbRW.inputeMirror(self.ids.queryMirror.text.split('\n'))
            self.mainClass.mirrorPic()

            toast(f"Saved!")
        else:
            toast('No new updated!')
        

class TimeoutSet(KitchenSinkBaseDialog):
    def __init__(self,updateText, **kwargs):
        super().__init__(**kwargs)


        self.timeoutD = dbRW.getConfig('timeoutD')[0]

        self.updateText = updateText
        self.ids.queryTimeout.text = str(self.timeoutD)


    
    def inputedTimeoutSave(self):
        setTimeout = int(self.ids.queryTimeout.text)
        if self.timeoutD != setTimeout:
            dbRW.updateConfig('timeoutD', setTimeout)
            self.updateText.text = f"Timeout : {setTimeout} seconds"
            toast(f"Saved! {setTimeout} seconds")
            self.dismiss()
        else:
            toast('No new updated!')

class FilesizeSet(KitchenSinkBaseDialog):
    def __init__(self,updateText, **kwargs):
        super().__init__(**kwargs)

        self.filesize = dbRW.getConfig('fileSize')[0]
        self.updateText = updateText
        self.ids.queryFilesize.text = str(self.filesize)


    
    def inputedFilesizeSave(self):
        setFilesize = int(self.ids.queryFilesize.text)
        if self.filesize != setFilesize:
            dbRW.updateConfig('fileSize', setFilesize)
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
