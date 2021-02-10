from os import environ
from os.path import join
from re import findall, sub
from datetime import datetime
from hurry.filesize import size
from libs.baseclass.database import MyDb
from libs.baseclass.utils import agoConv
from kivy.base import EventLoop

from kivy.uix.modalview import ModalView
from kivy.utils import get_color_from_hex, get_hex_from_color
from kivymd.color_definitions import colors, palette
from kivymd.theming import ThemableBehavior
from kivymd.toast import toast

from kivymd.icon_definitions import md_icons
from kivymd.uix.card import MDCardSwipe
from kivy.properties import StringProperty, ObjectProperty

class KitchenSinkBaseDialog(ThemableBehavior, ModalView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        # self.auto_dismiss = False
        self.dbRW = MyDb()

    # def hook_keyboard(self, window, key, *largs):
    #     if key == 27:
    #         # print("Back button clicked!")
    #         self.dismiss()
    #         # EventLoop.window.stop()
    #     return True 


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

        proxys = findall(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}[\s:\t][0-9]{1,5}",
        self.ids.query.text)
        for line in range(len(proxys)):
            proxys[line] = sub(r'[\s]', ':', proxys[line])
        if not proxys:
            toast(f"Save error!\nNo ip:port found!")
            self.ids.query.text = ""
            return False
        currentSave = ""
        for line in proxys:
            currentSave += line+'\n'
        
        IndexTime = datetime.now()
        self.dbRW.createProxysList(proxys, self.piced_pro, IndexTime)

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

        
        self.mirrors = self.dbRW.getAllMirrors()

        self.showsInBox = ""
        for m in self.mirrors:
            self.showsInBox += m[0]+'\n'
        self.ids.queryMirror.text = self.showsInBox


    
    def inputedMirrorSave(self):
        
        if self.showsInBox != self.ids.queryMirror.text:

            self.dbRW.inputeMirror(self.ids.queryMirror.text.split('\n'))
            self.mainClass.mirrorPic()

            toast(f"Saved!")
        else:
            toast('No new updated!')

class SwipeToDeleteItem(MDCardSwipe):
    text = StringProperty()
    remove_item = ObjectProperty()
    date_point = StringProperty()


class proxysDialogRemove(KitchenSinkBaseDialog):
    def __init__(self, mainClass, **kwargs):
        super().__init__(**kwargs)
        # self.filename = 'proxys.txt'
        self.mainClass = mainClass
        # if os.path.exists(self.filename):
        #     with open(self.filename, 'r', encoding="utf-8") as r:
        #         self.ids.query.text = r.read()

        
        proxysInx = [p[0] for p in self.dbRW.getProxysInx()][::-1]

        # self.showsInBox = ""
        # for m in self.mirrors:
        #     self.showsInBox += m[0]+'\n'
        # self.ids.queryMirror.text = self.showsInBox
        
        icons = list(md_icons.keys())
        for i,p in enumerate(proxysInx):
            self.ids.md_list.add_widget(
                SwipeToDeleteItem(text=f"#{i} {agoConv(p)}", remove_item=self.remove_item, date_point=p)
            )

    def remove_item(self, instance):
        point = instance.date_point
        currentPoint = self.dbRW.getConfig('proxysInx')[0]
        if self.dbRW.deletePoint('proxysInx', 'proxysInx', point) and self.dbRW.deletePoint('proxys', 'time', point):
            if point == currentPoint:
                self.dbRW.updateConfig('proxysInx', None)
                self.dbRW.updateConfig('miInx', 0)
                self.mainClass.configs['proxys'] = []
            # User feedback
            self.ids.md_list.remove_widget(instance)
            toast(f'"{instance.text}" has been successfully removed!')
            return True
        return False


class TimeoutSet(KitchenSinkBaseDialog):
    def __init__(self,updateText, **kwargs):
        super().__init__(**kwargs)


        self.timeoutD = self.dbRW.getConfig('timeoutD')[0]

        self.updateText = updateText
        self.ids.queryTimeout.text = str(self.timeoutD)


    
    def inputedTimeoutSave(self):
        setTimeout = int(self.ids.queryTimeout.text)
        if self.timeoutD != setTimeout:
            self.dbRW.updateConfig('timeoutD', setTimeout)
            self.updateText.text = f"Timeout : {setTimeout} seconds"
            toast(f"Saved! {setTimeout} seconds")
            self.dismiss()
        else:
            toast('No new updated!')

class FilesizeSet(KitchenSinkBaseDialog):
    def __init__(self,updateText, **kwargs):
        super().__init__(**kwargs)

        self.filesize = self.dbRW.getConfig('fileSize')[0]
        self.updateText = updateText
        self.ids.queryFilesize.text = str(self.filesize)


    
    def inputedFilesizeSave(self):
        setFilesize = int(self.ids.queryFilesize.text)
        if self.filesize != setFilesize:
            self.dbRW.updateConfig('fileSize', setFilesize)
            self.updateText.text = f"Filesize : {size(setFilesize)}"
            toast(f"Saved! {size(setFilesize)}")
            self.dismiss()
        else:
            toast('No new updated!')
        


class KitchenSinkDialogLicense(KitchenSinkBaseDialog):
    def on_open(self):
        with open(
            join(environ["KITCHEN_SINK_ROOT"], "LICENSE"),
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
