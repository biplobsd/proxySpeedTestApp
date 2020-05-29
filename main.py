import os
import sys

from kivy.lang import Builder
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
import kivymd.material_resources as m_res
from kivymd.font_definitions import theme_font_styles

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

if getattr(sys, "frozen", False):  # bundle mode with PyInstaller
    os.environ["KITCHEN_SINK_ROOT"] = sys._MEIPASS
else:
    sys.path.append(os.path.abspath(__file__).split("demos")[0])
    os.environ["KITCHEN_SINK_ROOT"] = os.path.dirname(os.path.abspath(__file__))
os.environ["KITCHEN_SINK_ASSETS"] = os.path.join(
    os.environ["KITCHEN_SINK_ROOT"], f"assets{os.sep}"
)
Window.softinput_mode = "below_target"
# _small = 3
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

class ProxySpeedTestApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.theme_style = "Dark"
        self.dialog_change_theme = None
        self.toolbar = None
        self.data_screens = {}
        self.scaning = Queue(maxsize=1)
        self.scaning.put_nowait(0)
        self.running = Queue(maxsize=1)
        self.running.put_nowait(0)
        self.currentSpeed = Queue()
        self.configs = {
            'protocol': 'http',
            'mirror': 'http://bd.archive.ubuntu.com/ubuntu/indices/override.oneiric.universe'}
        
        recentPlay = self.save_Update(filename='configs.json')
        if recentPlay:
            self.configs = recentPlay
        

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

    def build(self):
        Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/list_items.kv"
        )
        Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/dialog_change_theme.kv"
        )
        return Builder.load_file(
            f"{os.environ['KITCHEN_SINK_ROOT']}/libs/kv/start_screen.kv"
        )

    def show_dialog_change_theme(self):
        if not self.dialog_change_theme:
            self.dialog_change_theme = KitchenSinkDialogChangeTheme()
            self.dialog_change_theme.set_list_colors_themes()
        self.dialog_change_theme.open()

    def on_start(self):
        """Creates a list of items with examples on start screen."""

        sort = self.save_Update()
        if sort:
            self.show_List(sort)
            self.root.ids.Tproxys.text = f"Total proxys: {len(sort)}"
        else:
            self.root.ids.Tproxys.text = f"Total proxys: 0"
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"
        self.root.ids.Smirror.text = f"Mirror: {parse.urlparse(self.configs['mirror']).netloc}"
        
        
        
    def back_to_home_screen(self):
        self.root.ids.screen_manager.current = "home"

    
    def start_scan(self, instance):
        from kivy.utils import get_color_from_hex
        # print("Clicked!!")
        if instance.text == "Start":
            instance.text = "Stop"
            instance.md_bg_color = get_color_from_hex("#f44336")
            p = self.scaning.get_nowait()
            if not p == 1:
                self.scaning.put_nowait(1)
            else:
                self.scaning.put_nowait(p)
            Thread(target=self.proxySpeedTest, args=("start",)).start()
            # self.proxySpeedTest('start')
        else:
            p = self.scaning.get_nowait()
            if not p == 0:
                self.scaning.put_nowait(0)
            else:
                self.scaning.get_nowait(p)
            
            r = self.running.get_nowait()
            self.running.put_nowait(r)
            if not bool(r):
                instance.text = "Start"
                instance.md_bg_color = self.theme_cls.primary_color
            else:
                instance.text = "Stoping"
                instance.text_color
                instance.md_bg_color = get_color_from_hex("#757575")
            
    
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
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        self.currentSpeed.put_nowait(1024)
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
    
    def showupdate(self, idx, mode='u'):
        if mode == 'u':
            if idx == 1:
                self.root.ids.progressBar1.value += 1
            elif idx == 2:
                self.root.ids.progressBar2.value += 1
            elif idx == 3:
                self.root.ids.progressBar3.value += 1
        elif mode == 'd':
            if idx == 1:
                self.root.ids.progressBar1.value = 0
            elif idx == 2:
                self.root.ids.progressBar2.value = 0
            elif idx == 3:
                self.root.ids.progressBar3.value = 0
            self.root.ids.top_text.text = "0 KB/s"
    
    def proxySpeedTest(self, s):
        print(s)
        with open('proxys.txt', 'r') as r:
            data = r.read()
        data = data.split('\n')
        proxys = data[:-1]
        self.root.ids.Tproxys.text = f"Total proxys: {len(proxys)}"
        filename = 'chunk'
        protocol = self.configs['protocol']
        mirror = self.configs['mirror']
        unsort = list()
        sort = list ()
        self.root.ids.totalpb.max = len(proxys)
        self.root.ids.totalpb.value = 0
        for part in proxys:
            r = self.running.get()
            if not r == 1:
                self.running.put(1)
            else:
                self.running.put(r)
            s = self.scaning.get()
            self.scaning.put(s)
            if not bool(s):break        
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
            self.save_Update(sort)
            self.root.ids.backdrop_front_layer.data = []
            self.show_List(sort)
            self.root.ids.totalpb.value += 1
            comP = (self.root.ids.totalpb.value/len(proxys))*100
            self.root.ids.totalpbText.text = f"{round(comP)}%"
            # return True
        s = self.scaning.get()
        if not s == 0:
            self.scaning.put(0)
        else:
            self.scaning.put(s)
        self.root.ids.start_stop.text = "Start"
        self.root.ids.start_stop.md_bg_color = self.theme_cls.primary_color
        r = self.running.get()
        if not r == 0:
            self.running.put(0)
        else:
            self.running.put(r)
        print("Finished!")

    def show_List(self, data):
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
        from kivymd.toast import toast
        toast(f"Copied: {data}", duration=0.7)
        # print("Clicked!")
        Clipboard.copy(data)
    
    def speedcal(self, msg):
        print(msg)
        chunkSize = 0
        start = datetime.now()
        r = self.running.get()
        self.running.put(r)
        while bool(r):
            end = datetime.now()
            if .5 <= (end-start).seconds:
                delta = round(float((end - start).seconds) +
                            float(str('0.' + str((end -
                                                    start).microseconds))), 3)
                speed = round((chunkSize) / delta)
                start = datetime.now()
                chunkSize = 0
                if not speed <= 0:
                    self.root.ids.top_text.text = f"{size(speed, system=alternative)}/s"
            try:
                while True:
                    chunkSize += self.currentSpeed.get_nowait()
            except Empty:
                pass
            
            r = self.running.get()
            self.running.put(r)

ProxySpeedTestApp().run()