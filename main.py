import os
import sys

from kivy.lang import Builder

from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
import kivymd.material_resources as m_res
from kivymd.font_definitions import theme_font_styles
from kivymd.toast import toast
from kivy.utils import get_color_from_hex
from kivymd.uix.menu import MDDropdownMenu

from libs.baseclass.dialog_change_theme import KitchenSinkDialogChangeTheme
from libs.baseclass.list_items import KitchenSinkOneLineLeftIconItem

from datetime import datetime
from threading import Thread
import requests
from kivy.core.clipboard import Clipboard
from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    OptionProperty,
    BooleanProperty,
)
from kivy.metrics import dp
from urllib import parse
from queue import Empty, Queue
from hurry.filesize import alternative, size
import time
import sqlite3
from ago import human


# conn = sqlite3.connect('database.db')
# c = conn.cursor()
databaseFilename = 'database.db'

if platform == "android":
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

    Color = autoclass("android.graphics.Color")
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity


if getattr(sys, "frozen", False):  # bundle mode with PyInstaller
    os.environ["KITCHEN_SINK_ROOT"] = sys._MEIPASS
else:
    sys.path.append(os.path.abspath(__file__).split("demos")[0])
    os.environ["KITCHEN_SINK_ROOT"] = os.path.dirname(os.path.abspath(__file__))
    os.environ["KITCHEN_SINK_ASSETS"] = os.path.join(
    os.environ["KITCHEN_SINK_ROOT"], f"assets{os.sep}"
    )
# from kivy.core.window import Window
# Window.softinput_mode = "below_target"
# _small = 2
# Window.size = (1080/_small, 1920/_small)


class ProxyShowList(ThemableBehavior, RectangularRippleBehavior, ButtonBehavior, FloatLayout):
    """A one line list item."""

    _txt_top_pad = NumericProperty("16dp")
    _txt_bot_pad = NumericProperty("15dp")  # dp(20) - dp(5)
    _height = NumericProperty()
    _num_lines = 1
    
    text = StringProperty()
    text1 = StringProperty()
    text2 = StringProperty()
    text3 = StringProperty()

    text_color = ListProperty(None)

    theme_text_color = StringProperty("Primary", allownone=True)

    font_style = OptionProperty("Caption", options=theme_font_styles)


    divider = OptionProperty(
        "Full", options=["Full", "Inset", None], allownone=True
    )

    bg_color = ListProperty()

    _txt_left_pad = NumericProperty("16dp")
    _txt_top_pad = NumericProperty()
    _txt_bot_pad = NumericProperty()
    _txt_right_pad = NumericProperty(m_res.HORIZ_MARGINS)
    _num_lines = 3
    _no_ripple_effect = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = dp(48) if not self._height else self._height

def sec_to_mins(seconds):
    a = str(round((seconds % 3600)//60))
    b = str(round((seconds % 3600) % 60))
    d = f"{a} m {b} s"
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

class ProxySpeedTestApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "LightBlue"
        self.dialog_change_theme = None
        self.toolbar = None
        self.data_screens = {}
        self.scaning = Queue()
        self.running = Queue()
        self.currentSpeed = Queue()

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            try:
                c.execute("""create table proxys (
                    time datetime,
                    protocol text,
                    ip text,
                    size real,
                    getfiletime text,
                    speed integer
                    )""")
                
            except sqlite3.OperationalError as e:
                print(e)

            try:
                c.execute("create table proxysInx (proxysInx datetime)")
                # c.execute("INSERT INTO proxysInx VALUES (?)", [defaultIndexTime])
            except sqlite3.OperationalError as e:
                print(e)
            
            try:
                c.execute('''create table configs (
                    themeMode text,
                    miInx INTEGER,
                    proxysInx datetime
                    )''')
                c.execute("INSERT INTO configs (themeMode, miInx) VALUES ('Dark',0)")
            except sqlite3.OperationalError as e:
                print(e)
            
            try:
                c.execute("create table mirrors (mirror text)")
                c.execute("INSERT INTO mirrors VALUES ('http://bd.archive.ubuntu.com/ubuntu/indices/override.oneiric.universe')")
                c.execute("INSERT INTO mirrors VALUES ('http://provo.speed.googlefiber.net:3004/download?size=1048576')")
            except sqlite3.OperationalError as e:
                print(e)
            
            c.execute("SELECT * FROM 'configs'")
            configs = c.fetchall()
            c.execute("SELECT * FROM 'mirrors'")
            mirrors = c.fetchall()
            self.selLId = configs[0][2]
            if self.selLId:
                c.execute("SELECT ip, size, getfiletime, speed FROM 'proxys' WHERE time=?", [self.selLId])
                scan_list = c.fetchall()
                c.execute("SELECT ip FROM 'proxys' WHERE time=?", [self.selLId])
                getips = c.fetchall()
                c.execute("SELECT protocol FROM 'proxys' WHERE time=?", [self.selLId])
                protocol = c.fetchone()[0]
        conn.commit()
        conn.close()

        self.scan_list = []
        if self.selLId:
            for l in scan_list:
                if not None in l:
                    self.scan_list.append({"IP": l[0], "SIZE": l[1], "TIME": l[2], "SPEED": l[3]})
        # print(mirrors)
        # print(configs)
        
            
        self.proxys = [ip[0] for ip in getips] if self.selLId else []
        self.theme_cls.theme_style = configs[0][0]
        self.mirrors = mirrors
        # self.mirrorMenu = [{"icon": "web", "text": parse.urlparse(mirror[0]).netloc} for mirror[0] in mirrors]
        self.miInx = configs[0][1]
        self.configs = {
            'protocol': protocol if self.selLId else 'http',
            'mirror': mirrors[self.miInx][0]}
        self.proxysInx = []
        # recentPlay = self.save_Update(filename='configs.json')

        
    def changeThemeMode(self, inst):
        self.theme_cls.theme_style = inst

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("UPDATE 'configs' SET themeMode=?", [inst])
        conn.commit()
        conn.close()

    def save_Update(self, l=[], filename='scan_data.json'):
        import json
        if l:
            with open(filename, 'w') as write:
                json.dump(l, write, indent=4)
        else:
            if os.path.exists(filename):
                with open(filename, 'r') as read:
                    return json.load(read)
            else:
                return False
    
    def save_UpdateDB(self, l=[]):
      
        if not l:return False
        # print(l)
        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            try:
                for p in l:
                    c.execute("UPDATE proxys SET size=?, getfiletime=?, speed=? WHERE ip=?",
                                                (p['SIZE'], p['TIME'], p['SPEED'], p['IP']))
            except sqlite3.OperationalError as e:
                print(e)
        conn.commit()
        conn.close()

    def build(self):
        if platform == "android":
            self._statusBarColor()
        Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/list_items.kv"
        )
        Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/dialog_change_theme.kv"
        )
        return Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/start_screen.kv"
        )

    @run_on_ui_thread
    def _statusBarColor(self, color="#03A9F4"):
        
        window = activity.getWindow()
        window.clearFlags(WindowManager.FLAG_TRANSLUCENT_STATUS)
        window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
        window.setStatusBarColor(Color.parseColor(color)) 
        window.setNavigationBarColor(Color.parseColor(color))


    def show_dialog_change_theme(self):
        if not self.dialog_change_theme:
            self.dialog_change_theme = KitchenSinkDialogChangeTheme()
            self.dialog_change_theme.set_list_colors_themes()
        self.dialog_change_theme.open()

    def on_start(self):
        """Creates a list of items with examples on start screen."""

        unsort = self.scan_list
        # print(unsort)
        if unsort:
            sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
            self.show_List(sort)
            self.root.ids.Tproxys.text = f"Total proxys: {len(sort)}"
        else:
            self.root.ids.Tproxys.text = f"Total proxys: 0"
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        self.root.ids.Smirror.text = f"Mirror: {parse.urlparse(self.configs['mirror']).netloc}".upper()
        # self.root.ids.backdrop._front_layer_open=True
        
        self.mirrorPic()
        self.protPic()
        self.listPic()

    def listPic(self):

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("SELECT proxysInx FROM 'proxysInx'")
            proxysInx = c.fetchall()

            c.execute("SELECT  proxysInx FROM 'configs'")
            self.selLId = c.fetchone()[0]
        conn.commit()
        conn.close()

        self.proxysInx = proxysInx
        
        if proxysInx:
            selLIdindxDict = {}
            self.ListItems = []
            i = 0
            for Inx in proxysInx:
                self.ListItems.append({"icon": "playlist-remove", "text": f'#{i} '+agoConv(Inx[0])})
                selLIdindxDict[Inx[0]] = i
                i += 1
        else:
            self.ListItems = [{"icon": "playlist-remove", "text": "None"}]
        
        if proxysInx:
            self.selLIdindx = selLIdindxDict[self.selLId]
        self.root.ids.Slist.text = f"list : #{self.selLIdindx} {agoConv(self.selLId)}".upper() if proxysInx else "list :"

        self.listSel = MDDropdownMenu(
            caller=self.root.ids.Slist, items=self.ListItems, width_mult=3,
            opening_time=0.2,
            use_icon_item=False,
            position='auto',
            max_height=0,
            callback=self.set_list,
        )

    def set_list(self, ins):
        import re
        self.selLIdindx = int(re.search(r'#(\d)\s', ins.text).group(1))
        withoutHash = re.search(r'#\d\s(.+)', ins.text).group(1)
        print(self.selLIdindx)

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("SELECT proxysInx FROM 'proxysInx'")
            proxysInx = c.fetchall()
            self.selLId = proxysInx[self.selLIdindx][0]
            c.execute("SELECT ip FROM 'proxys' WHERE time=?", [self.selLId])
            getips = c.fetchall()
            c.execute("SELECT protocol FROM 'proxys' WHERE time=?", [self.selLId])
            protocol = c.fetchone()[0]
            c.execute("UPDATE 'configs' SET proxysInx=?", [self.selLId])
            
            c.execute("SELECT ip, size, getfiletime, speed FROM 'proxys' WHERE time=?", [self.selLId])
            scan_list = c.fetchall()
            # print(protocol)
        conn.commit()
        conn.close()

        self.scan_list = []
        if self.selLId:
            for l in scan_list:
                if not None in l:
                    self.scan_list.append({"IP": l[0], "SIZE": l[1], "TIME": l[2], "SPEED": l[3]})

        unsort = self.scan_list
        if unsort:
            sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
            # print(sort)
            self.show_List(sort)

        self.proxys = [ip[0] for ip in getips]
        self.configs['protocol'] = protocol

        self.root.ids.Slist.text = f"list : {ins.text}".upper()
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        self.root.ids.Tproxys.text = f"Total proxys: {len(self.proxys)}"
        
        # print(getips)
        toast(ins.text)
        # print(indx)
        self.listSel.dismiss()


    def protPic(self):
        items = [{"icon": "protocol", "text": protocol.upper()} for protocol in ['http', 'https', 'socks4', 'socks5']]
        self.protSel = MDDropdownMenu(
            caller=self.root.ids.Sprotocol, items=items, width_mult=2,
            opening_time=0.2,
            use_icon_item=False,
            position='auto',
            callback=self.set_protocol
        )

    def set_protocol(self, ins):
        # print(self.mirrors[0])
        # print(miInx)
        self.configs['protocol'] = ins.text.lower()
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        
        toast(self.configs['protocol'])
        self.protSel.dismiss()

    def mirrorPic(self):

        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("SELECT * FROM 'mirrors'")
            mirrors = c.fetchall()
        conn.commit()
        conn.close()

        self.mirrors = mirrors
        items = [{"icon": "web", "text": parse.urlparse(mirror[0]).netloc} for mirror in mirrors]
        self.mirrSel = MDDropdownMenu(
            caller=self.root.ids.Smirror, items=items, width_mult=5,
            opening_time=0.2,
            use_icon_item=False,
            position='bottom',
            max_height=0,
            callback=self.set_mirror,
        )

    def set_mirror(self, ins):
        miInx = 0
        for l in self.mirrors:
            if ins.text in l[0]:
                break
            miInx += 1
        
        self.configs['mirror'] = self.mirrors[miInx][0]
        self.root.ids.Smirror.text = f"Mirror: {ins.text}".upper()
        
        conn = sqlite3.connect(databaseFilename)
        c = conn.cursor()
        with conn:
            c.execute("UPDATE 'configs' SET proxysInx=?", [self.selLId])
            c.execute("UPDATE 'configs' SET miInx=? WHERE miInx=?", (miInx, self.miInx))
        conn.commit()
        conn.close()
        
        toast(self.configs['mirror'])
        self.mirrSel.dismiss()
        

    def start_scan(self, instance):
        # print("Clicked!!")
        if instance.text == "Start":
            
            self.root.ids.Tproxys.text = f"Total proxys: {len(self.proxys)}"
            if len(self.proxys) == 0:
                toast("First input proxys ip:port list then start scan.")
                return

            instance.text = "Stop"
            color = "#f44336"
            instance.md_bg_color = get_color_from_hex(color)
            self.theme_cls.primary_palette = "Red"
            if platform == "android":self._statusBarColor(color)
            self.scaning.put_nowait(1)
            self.running.put_nowait(1)
            
            conn = sqlite3.connect(databaseFilename)
            c = conn.cursor()
            with conn:
                IndexTime = datetime.now()
                c.execute("UPDATE 'configs' SET proxysInx=?", [IndexTime])
                c.execute("UPDATE 'proxysInx' SET proxysInx=? WHERE proxysInx=?", (IndexTime, self.selLId))
                c.execute("UPDATE 'proxys' SET time=?, size=NULL, getfiletime=NULL, speed=NULL WHERE time=?", (IndexTime, self.selLId))
            conn.commit()
            conn.close()
            
            self.selLId = str(IndexTime)

            Thread(target=self.proxySpeedTest, args=(
                self.proxys,
                self.configs['protocol'],
                self.configs['mirror'],
                )).start()
        
            # self.proxySpeedTest('start')
        elif instance.text == "Stoping":
            toast(f"Waiting for finish {self.root.ids.currentIP.text[8:]}!")
        else:
            while not self.scaning.empty():
                self.scaning.get_nowait()
            

            if not self.running.empty():
                instance.text = "Stoping"
                # instance.text_color
                color = "#757575"
                instance.md_bg_color = get_color_from_hex(color)
                self.theme_cls.primary_palette = "Gray"
                if platform == "android":self._statusBarColor(color)
            
    
    def downloadChunk(self, idx, proxy_ip, filename, mirror, protocol):
        file_size = 1062124 
        print(f'{idx} Started')
        try:
            if protocol == 'http':
                proxies = {
                    'http': f'http://{proxy_ip}',
                    'https': f'http://{proxy_ip}'
                }
            elif protocol == 'https':
                proxies = {
                    'http': f'https://{proxy_ip}',
                    'https': f'https://{proxy_ip}'
                }
            elif protocol == 'socks4':
                proxies = {
                    'http': f'socks4://{proxy_ip}',
                    'https': f'socks4://{proxy_ip}'
                }
            elif protocol == 'socks5':
                proxies = {
                    'http': f'socks5://{proxy_ip}',
                    'https': f'socks5://{proxy_ip}'
                }

            req = requests.get(
                mirror,
                headers={"Range": "bytes=%s-%s" % (0, file_size)},
                stream=True,
                proxies=proxies,
                timeout=5
            )
            with(open(f'{filename}{idx}', 'ab')) as f:
                start = datetime.now()
                chunkSize = 0
                oldSpeed = 0
                chunkSizeUp = 1024
                for chunk in req.iter_content(chunk_size=chunkSizeUp):
                    end = datetime.now()
                    if 0.1 <= (end-start).seconds:
                        delta = round(float((end - start).seconds) +
                                    float(str('0.' + str((end -
                                                            start).microseconds))), 3)
                        speed = round((chunkSize) / delta)
                        # if oldSpeed < speed:
                            # chunkSizeUp *= 3
                        # else:
                        #     chunkSizeUp = speed
                        oldSpeed = speed
                        start = datetime.now()
                        self.currentSpeed.put_nowait(speed)
                        chunkSize = 0
                    if chunk:
                        chunkSize += sys.getsizeof(chunk)
                        self.showupdate(idx)
                        f.write(chunk)
        except requests.exceptions.ProxyError:
            self.showupdate(idx, 'd')
            print(f"\nThread {idx}. Could not connect to {proxy_ip}")
            return False
        except requests.exceptions.ConnectionError:
            self.showupdate(idx, 'd')
            print(f"\nThread {idx}. Could not connect to {proxy_ip}")
            return False
        except IndexError:
            self.showupdate(idx, 'd')
            print(f'\nThread {idx}. You must provide a testing IP:PORT proxy')
            return False
        except requests.exceptions.ConnectTimeout:
            self.showupdate(idx, 'd')
            print(f"\nThread {idx}. ConnectTimeou for {proxy_ip}")
            return False
        except requests.exceptions.ReadTimeout:
            self.showupdate(idx, 'd')
            print(f"\nThread {idx}. ReadTimeout for {proxy_ip}")
            return False
        except RuntimeError:
            self.showupdate(idx, 'd')
            print(f"\nThread {idx}. Set changed size during iteration. {proxy_ip}")
            return False
        except KeyboardInterrupt:
            self.showupdate(idx, 'd')
            print(f"\nThread no: {idx}. Exited by User.")
        
        self.showupdate(idx, 'd')
    
    def showupdate(self, idx, mode='u', error=True):
        if mode == 'u':
            if idx == 1:
                self.root.ids.progressBar1.value += 1
            elif idx == 2:
                self.root.ids.progressBar2.value += 1
            elif idx == 3:
                self.root.ids.progressBar3.value += 1
        elif mode == 'd':
            color = "#f44336"
            if idx == 1:
                self.root.ids.progressBar1.value = 0
                # if error:
                #     self.root.ids.progressBar1.color = get_color_from_hex(color)
            elif idx == 2:
                self.root.ids.progressBar2.value = 0
                # if error:
                #     self.root.ids.progressBar1.color = get_color_from_hex(color)
            elif idx == 3:
                self.root.ids.progressBar3.value = 0
                # if error:
                #     self.root.ids.progressBar1.color = get_color_from_hex(color)
            self.root.ids.top_text.text = "0 KB/s"
    
    def proxySpeedTest(self, proxys, protocol, mirror):
        filename = 'chunk'
        unsort = list()
        sort = list ()
        self.root.ids.totalpb.max = len(proxys)
        self.root.ids.totalpb.value = 0
        print(proxys)
        for part in proxys:
            if self.scaning.empty():break        
            proxy_ip = part.strip()
            self.root.ids.currentIP.text = f"CURRENT: {proxy_ip}"
            # Removing before test chunk file
            for i in range(3):
                if os.path.exists(f'{filename}{i}'):
                    os.remove(f'{filename}{i}')

            # Starting chunk file downloading
            timeStart = datetime.now()
            print("Starting ....")
            Thread(target=self.speedcal, args=('start',)).start()
            downloaders = [
            Thread(
                target=self.downloadChunk,
                args=(idx, proxy_ip, filename, mirror, protocol),
            )
            for idx in range(3)]
            for _ in downloaders:_.start()
            for _ in downloaders:_.join()
            timeEnd = datetime.now()

            filesize = 0
            for i in range(3):
                try:
                    filesize = filesize + os.path.getsize(f'{filename}{i}')
                except FileNotFoundError:
                    continue

            filesizeM = round(filesize / pow(1024, 2), 2)
            delta = round(float((timeEnd - timeStart).seconds) +
                        float(str('0.' + str((timeEnd -
                                                timeStart).microseconds))), 3)
            speed = round(filesize / 1024) / delta

            for i in range(3):
                if os.path.exists(f'{filename}{i}'):
                    os.remove(f'{filename}{i}')

            unsort.append(
                {'IP': proxy_ip,
                'SIZE': filesizeM, 
                'TIME': sec_to_mins(delta),
                'SPEED': int(speed)}
                )
            sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
            self.save_UpdateDB(sort)
            self.show_List(sort)
            self.root.ids.totalpb.value += 1
            comP = (self.root.ids.totalpb.value/len(proxys))*100
            self.root.ids.totalpbText.text = f"{round(comP)}%"
            self.root.ids.Slist.text = f"list : #{self.selLIdindx} {agoConv(self.selLId)}".upper()
            # return True
        
        self.root.ids.start_stop.text = "Start"
        self.theme_cls.primary_palette = "LightBlue"
        self.root.ids.start_stop.md_bg_color = self.theme_cls.primary_color
        if platform == "android":self._statusBarColor()
        while not self.running.empty():
            self.running.get_nowait()
        print("Finished!")

    def show_List(self, data):
        self.root.ids.backdrop_front_layer.data = []
        for parServer in data:
            self.root.ids.backdrop_front_layer.data.append(
                {
                    "viewclass": "ProxyShowList",
                    "text": parServer['IP'],
                    "text1": f"{parServer['SIZE']} MB",
                    "text2": parServer['TIME'],
                    "text3": f"{parServer['SPEED']} KB/s",
                    "on_release": lambda x=parServer['IP']: self.copy_proxyip(x),
                }
                )
    def copy_proxyip(self, data):
        toast(f"Copied: {data}")
        Clipboard.copy(data)
    
    def speedcal(self, msg):
        print(msg)
        speed = 0
        start = datetime.now()
        oldspeed = 0
        while not self.running.empty():
            end = datetime.now()
            if (0.1 <= (end-start).seconds) and speed != 0 and oldspeed != speed:
                self.root.ids.top_text.text = f"{size(speed, system=alternative)}/s"
                start = datetime.now()
                oldspeed = speed
                speed = 0
            try:
                while not self.currentSpeed.empty():
                    speed += self.currentSpeed.get_nowait()
            except Empty:
                pass

if __name__ == "__main__":
    ProxySpeedTestApp().run()