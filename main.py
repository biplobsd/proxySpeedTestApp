import re
import sys
from os import environ, sep, remove
from os.path import join, abspath, dirname, exists, getsize
from datetime import datetime

from kivy.lang import Builder
from kivy.utils import platform
from kivy.logger import Logger, LOG_LEVELS
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.utils import get_color_from_hex
from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    OptionProperty,
    BooleanProperty,
    ObjectProperty
)
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.base import EventLoop
from kivy.config import Config

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivymd.font_definitions import theme_font_styles
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import (
    MDFlatButton, MDRaisedButton, MDFloatingActionButton
)
from kivymd.color_definitions import colors
from kivymd.uix.taptargetview import MDTapTargetView
from kivymd.uix.behaviors import MagicBehavior, HoverBehavior

from libs.baseclass.dialog_change_theme import KitchenSinkDialogChangeTheme
from libs.baseclass.dialog_change_theme import PSTDialogInput
from libs.baseclass.list_items import ProxysDialogHistory
from libs.baseclass.database import MyDb
from libs.baseclass.utils import open_link
from libs.baseclass.utils import agoConv
from libs.baseclass.utils import sec_to_mins

from threading import Thread
from requests import get
from requests.exceptions import (
    ProxyError, ConnectTimeout, ReadTimeout, ConnectionError as connError
)
from urllib import parse
from urllib3 import disable_warnings, exceptions
from queue import Empty, Queue
from hurry.filesize import alternative, size
from functools import partial

__version__ = "1.6"
Logger.setLevel(LOG_LEVELS['debug'])
Config.set('graphics', 'verify_gl_main_thread', False)
disable_warnings(exceptions.InsecureRequestWarning)

if platform == "android":
    # from kivmob import KivMob, TestIds
    from android.runnable import run_on_ui_thread  # type: ignore
    from jnius import autoclass  # type: ignore

    Color = autoclass("android.graphics.Color")
    WindowManager = autoclass('android.view.WindowManager$LayoutParams')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
else:
    def run_on_ui_thread(_):
        pass

if getattr(sys, "frozen", False):  # bundle mode with PyInstaller
    environ["KITCHEN_SINK_ROOT"] = sys._MEIPASS
    environ["KITCHEN_SINK_ASSETS"] = join(
        environ["KITCHEN_SINK_ROOT"], f"assets{sep}"
    )
    # Logger.info("___one___")
else:
    sys.path.append(abspath(__file__).split("ProxySpeedTestV2")[0])
    environ["KITCHEN_SINK_ROOT"] = dirname(abspath(__file__))
    environ["KITCHEN_SINK_ASSETS"] = join(
        environ["KITCHEN_SINK_ROOT"], f"assets{sep}"
    )
    # Logger.info("___two___")

# from kivy.core.window import Window
# Window.softinput_mode = "below_target"
# _small = 2
# Window.size = (1080/_small, 1920/_small)

# class adMobIds:

#     """ Test AdMob App ID """
#     APP = "ca-app-pub-3940256099942544~3347511713"

#     """ Test Banner Ad ID """
#     BANNER = "ca-app-pub-3940256099942544/6300978111"

    # """ Test Interstitial Ad ID """
    # INTERSTITIAL = "ca-app-pub-3940256099942544/1033173712"

    # """ Test Interstitial Video Ad ID """
    # INTERSTITIAL_VIDEO = "ca-app-pub-3940256099942544/8691691433"

    # """ Test Rewarded Video Ad ID """
    # REWARDED_VIDEO = "ca-app-pub-3940256099942544/5224354917"


class PSTBackdropBackLayer(FloatLayout):
    backdrop = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        EventLoop.window.bind(on_keyboard=self.hk)

    def hk(self, window, key, *largs):
        if key == 27:
            # print("Back button clicked!")
            if self.backdrop._front_layer_open:
                self.backdrop.left_action_items = [
                    ['menu', lambda x: self.backdrop.open()]
                ]
                self.backdrop.close()
        return True


class ProxyShowList(
        ThemableBehavior, RectangularRippleBehavior,
        ButtonBehavior, HoverBehavior, FloatLayout):
    """A one line list item."""

    _txt_top_pad = NumericProperty()
    _txt_bot_pad = NumericProperty()  # dp(20) - dp(5)
    _height = NumericProperty()
    _num_lines = 1

    text = StringProperty()
    text1 = StringProperty()
    text2 = StringProperty()
    text3 = StringProperty()
    text4 = StringProperty()

    text_color = ListProperty(None)

    theme_text_color = StringProperty("Secondary", allownone=True)

    font_style = OptionProperty("Caption", options=theme_font_styles)

    divider = OptionProperty(
        "Full", options=["Full", "Inset", None], allownone=True
    )

    bg_color = ListProperty()

    _txt_left_pad = NumericProperty()
    _txt_right_pad = NumericProperty()
    _num_lines = 3
    _no_ripple_effect = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = dp(48) if not self._height else self._height

    def _enter(self, ins):
        '''The method will be called when the mouse cursor
        is within the borders of the current widget.'''

        bg_color = self.theme_cls.divider_color
        bg_color[3] = 0.05
        ins.bg_color = bg_color

    def _leave(self, ins):
        '''The method will be called when the mouse cursor goes beyond
        the borders of the current widget.'''
        ins.bg_color = []


class MagicButton(MagicBehavior, MDFloatingActionButton):
    text = StringProperty()


class ProxySpeedTestApp(MDApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon = f"{environ['KITCHEN_SINK_ASSETS']}icon.png"
        self.version = __version__
        self.theme_cls.primary_palette = "LightBlue"
        self.dialog_change_theme = None
        self.toolbar = None
        self.scaning = Queue()
        self.running = Queue()
        self.currentSpeed = Queue()
        self.forceStop = Queue()

        self.pbar0 = Queue()
        self.pbar1 = Queue()
        self.pbar2 = Queue()
        self.totalpb = Queue()
        self.configsUpdate()

    # def on_resume(self):
    #     self.ads.request_interstitial()

    def configsUpdate(self):
        configs = dbRW.getAllConfigs()
        mirrors = dbRW.getAllMirrors()
        self.selLId = configs[0][2]
        getips = None
        protocol = None
        totalScan = None

        if self.selLId:
            totalScan = dbRW.getProxysInxTS(self.selLId)[0]
            getips = dbRW.getAllCurrentProxys(self.selLId)
            protocol = getips[0][4]

        self.scan_list = []
        if self.selLId:
            for slist in getips:
                if not (None in slist):
                    self.scan_list.append({
                        "IP": slist[0],
                        "SIZE": slist[1],
                        "TIME": slist[2],
                        "SPEED": slist[3],
                        "top3c": slist[6]})

        self.theme_cls.theme_style = configs[0][0]

        miInx = configs[0][1]
        self.configs = {
            'protocol': protocol if self.selLId else 'http',
            'mirror': mirrors[miInx][0],
            'timeout': int(configs[0][3]),
            'fileSize': int(configs[0][4]),
            'miInx': miInx,
            'proxysInx': [],
            'mirrors': mirrors,
            'proxys': getips if self.selLId else[],
            'totalScan': totalScan if self.selLId else 0,
            'autoKill': int(configs[0][5]),
            'autoKillMode': int(configs[0][6])
        }

    def changeThemeMode(self, inst):
        self.theme_cls.theme_style = inst

        dbRW.updateThemeMode(inst)

    def checkUpdates(self, ava=False, d=False):
        upCURL = 'https://raw.githubusercontent.com/biplobsd/proxySpeedTestApp/master/updates.json'  # noqa update-check-link
        # from json import load
        # with open('updates.json', 'r') as read:
        #     updateinfo = load(read)
        # toast("Checking for any updates ...")
        try:
            updateinfo = get(upCURL, verify=False, timeout=1).json()
        except:  # noqa
            toast("Unable to get updates information")
            return False
        try:
            appLink = updateinfo["release"][platform]
        except KeyError:
            appLink = ""
        title = f"App update v{updateinfo['version']} {platform}"
        msg = "You are already in latest version!"
        b1 = "CENCEL"
        force = False

        if updateinfo['version'] > float(self.version) and appLink != "":
            if updateinfo['messages']:
                title = updateinfo['messages']
            msg = ""
            b2 = "DOWNLOAD"
            force = bool(updateinfo['force'])
            if force:
                b1 = "EXIT"
            ava = True
        else:
            b2 = "CHECK"

        self.updateDialog = MDDialog(
            title=title,
            text=msg+updateinfo[
                'changelogs']+f"\n\n[size=15]Force update: {force}[/size]",
            auto_dismiss=False,
            buttons=[
                MDFlatButton(
                    text=b1,
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x:self.updateDialog.dismiss() if b1 == "CENCEL" else self.stop()  # noqa
                ),
                MDRaisedButton(
                    text=b2,
                    on_release=lambda x:open_link(appLink) if b2 == "DOWNLOAD" else self.FCU(self.updateDialog),  # noqa
                    text_color=self.theme_cls.primary_light,
                ),
            ],
        )
        self.updateDialog.ids.title.theme_text_color = "Custom"
        self.updateDialog.ids.title.text_color = self.theme_cls.primary_light  # noqa
        if ava:
            self.updateDialog.open()

    def FCU(self, inst):
        inst.dismiss()
        Clock.schedule_once(partial(self.checkUpdates, True), -1)

    def on_pause(self):
        return True

    def save_UpdateDB(self, lists=[], addHistory=[]):
        dbRW = MyDb()
        if lists:
            dbRW.updateScanList(lists, self.selLId)
        if addHistory:
            hotData, protocol, mirror = addHistory
            dbRW.inputProxyHistory(hotData, protocol, mirror)

    def build(self):
        if platform == "android":
            self._statusBarColor()
        Builder.load_file(
            f"{environ['KITCHEN_SINK_ROOT']}/libs/kv/list_items.kv"
        )
        Builder.load_file(
            f"{environ['KITCHEN_SINK_ROOT']}/libs/kv/dialog_change_theme.kv"
        )

        return Builder.load_file(
            f"{environ['KITCHEN_SINK_ROOT']}/libs/kv/start_screen.kv"
        )

    @run_on_ui_thread
    def _statusBarColor(self, color="#03A9F4"):

        window = activity.getWindow()
        window.clearFlags(WindowManager.FLAG_TRANSLUCENT_STATUS)
        window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
        window.setStatusBarColor(Color.parseColor(color))
        window.setNavigationBarColor(Color.parseColor(color))

    @run_on_ui_thread
    def _wakeScreen(self, mode="on"):
        window = activity.getWindow()
        if mode == "on":
            window.addFlags(WindowManager.FLAG_KEEP_SCREEN_ON)
        elif mode == "off":
            window.clearFlags(WindowManager.FLAG_KEEP_SCREEN_ON)

    def show_dialog_change_theme(self):
        if not self.dialog_change_theme:
            self.dialog_change_theme = KitchenSinkDialogChangeTheme()
            self.dialog_change_theme.set_list_colors_themes()
        self.dialog_change_theme.open()

    def on_start(self):
        """Creates a list of items with examples on start screen."""
        unsort = self.scan_list
        # print(unsort)
        self.show_List()
        if unsort:
            sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
            # print(sort)
            self.show_List(sort)
            self.root.ids.Tproxys.text = f"proxys: {len(sort)}"
            self.root.ids.Tscan.text = f"scan: {self.configs['totalScan']}"
        else:
            self.root.ids.Tscan.text = "scan: 0"
            self.root.ids.Tproxys.text = "proxys: 0"
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"  # noqa
        # self.root.ids.backdrop._front_layer_open=True
        Logger.info(f"Platform: {platform}")
        # if platform == 'android':
        # self.ads = KivMob(adMobIds.APP)
        # self.ads.new_banner(adMobIds.BANNER, top_pos=False)
        # self.ads.request_banner()
        # self.ads.show_banner()

        # self.root.ids.adsShow.size = (self.root.ids.backdrop_front_layer.width, 110) # noqa

        self.protPic()
        self.listPic()
        self.tap_target_list_view = MDTapTargetView(
            widget=self.root.ids.Slist,
            title_text="Pic a lists",
            description_text="Your selected list choice will be saved in database!",  # noqa
            widget_position="right_top",
            # outer_radius=dp(320),
            cancelable=True,
            outer_circle_color=self.theme_cls.primary_color[:-1],
            outer_circle_alpha=0.9,
        )
        Thread(target=self.checkUpdates).start()
        self.root.ids.backdrop.ids.header_button.height = 0

    def listPic(self):
        proxysInx = dbRW.getProxysInx()[::-1]
        self.selLId = dbRW.getConfig('proxysInx')[0]
        Logger.debug(self.selLId)
        self.configs['proxysInx'] = proxysInx
        selLIdindxDict = {}
        self.ListItems = []

        if proxysInx:
            for i, Inx in enumerate(proxysInx):
                IPs = len(dbRW.getAllCurrentProxys((Inx[0])))
                intext = f'#{i} '+f'{IPs}ip '+agoConv(Inx[0])
                self.ListItems.append({
                    "text": intext,
                    "viewclass": "MenuOneLineListItem",
                    "on_release":
                        lambda x=intext:
                        self.set_list(x)
                })
                selLIdindxDict[Inx[0]] = i
        else:
            self.ListItems = [{
                "text": "None",
                "font_style": "Caption",
                "top_pad": 35,
                "bot_pad": 10}]

        if self.selLId:
            self.selLIdindx = selLIdindxDict[self.selLId]
        self.root.ids.lastScan.text = agoConv(self.selLId).upper()
        self.root.ids.Slist.text = f"list : #{self.selLIdindx}".upper() if self.selLId else "list :"  # noqa

        self.listSel = MDDropdownMenu(
            caller=self.root.ids.Slist,
            items=self.ListItems,
            width_mult=3,
            opening_time=0.2,
            position='auto',
            max_height=dp(50*len(self.ListItems))
        )
        self.listSel.bind(
            on_release=self.set_list,
            on_dismiss=self.manuDismiss)

    def manuDismiss(self, ins):
        ins.caller.custom_color = get_color_from_hex(
            colors[self.theme_cls.primary_palette]["300"])

    def set_list(self, ins, insMain=""):
        if insMain:
            ins = insMain.text
        self.selLIdindx = int(re.search(r'#(\d+)\s', ins).group(1))
        # withoutHash = re.search(r'#\d\s(.+)', ins.text).group(1)
        Logger.debug(self.selLIdindx)

        proxysInx = sorted(dbRW.getProxysInx(), reverse=True)
        self.selLId = proxysInx[self.selLIdindx][0]
        proxys = dbRW.getAllCurrentProxys(self.selLId)
        self.configs['totalScan'] = dbRW.getProxysInxTS(self.selLId)[0]
        protocol = proxys[0][4]
        dbRW.updateConfig("proxysInx", self.selLId)
        scan_list = proxys

        self.scan_list = []
        if self.selLId:
            for slist in scan_list:
                if not (None in slist):
                    self.scan_list.append({
                        "IP": slist[0],
                        "SIZE": slist[1],
                        "TIME": slist[2],
                        "SPEED": slist[3],
                        "top3c": slist[6]
                    })

        unsort = self.scan_list
        # if unsort:
        sort = sorted(unsort, key=lambda x: x['SPEED'], reverse=True)
        # print(sort)
        # self.show_List()
        self.show_List(sort)

        self.configs['proxys'] = proxys
        self.configs['protocol'] = protocol

        self.root.ids.lastScan.text = agoConv(self.selLId).upper()
        self.root.ids.Slist.text = f"list : #{self.selLIdindx}".upper()
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"  # noqa
        self.root.ids.Tproxys.text = f"proxys: {len(self.configs['proxys'])}"
        self.root.ids.Tscan.text = f"scan: {self.configs['totalScan']}"

        # print(getips)
        toast(ins)
        # print(indx)
        self.listSel.dismiss()
        if self.tap_target_list_view.state == 'open':
            self.tap_target_list_view.stop()

    def protPic(self):
        items = [{
            "text": protocol.upper(),
            "viewclass": "MenuOneLineListItem",
            "on_release": lambda x=protocol: self.set_protocol(x)}
            for protocol in [
                'http', 'https', 'socks4', 'socks5']]
        self.protSel = MDDropdownMenu(
            caller=self.root.ids.Sprotocol,
            items=items,
            width_mult=2,
            opening_time=0.2,
            position='auto',
            max_height=dp(50*len(items))
        )
        self.protSel.bind(
            on_release=self.set_protocol,
            on_dismiss=self.manuDismiss)

    def set_protocol(self, ins, insMain=""):
        if insMain:
            ins = insMain.text
        self.configs['protocol'] = ins.lower()
        self.root.ids.Sprotocol.text = f"Protocol: {self.configs['protocol'].upper()}"  # noqa

        toast(self.configs['protocol'])
        self.protSel.dismiss()

    def mirrorPic(self):

        mirrors = dbRW.getAllMirrors()

        self.configs['mirrors'] = mirrors
        items = [{
            "text": parse.urlparse(mirror[0]).netloc,
            "viewclass": "MenuOneLineListItem",
            "on_release": lambda x=parse.urlparse(mirror[0]).netloc:
                 self.set_mirror(x)} for mirror in mirrors]
        self.mirrSel = MDDropdownMenu(
            caller=self.root.ids.backlayer.ids.Smirror,
            items=items,
            opening_time=0.2,
            width_mult=5,
            position='auto',
            max_height=dp(50*len(items))
        )
        self.mirrSel.bind(
            on_dismiss=self.manuDismiss)

    def set_mirror(self, ins):
        miInx = 0
        for lists in self.configs['mirrors']:
            if ins == parse.urlparse(lists[0]).netloc:
                break
            miInx += 1

        self.configs['mirror'] = self.configs['mirrors'][miInx][0]
        self.root.ids.backlayer.ids.Smirror.text = f"Mirror: {ins}"
        dbRW.updateConfig("proxysInx", self.selLId)
        dbRW.updateConfig("miInx", miInx)

        toast(self.configs['mirror'])
        self.mirrSel.dismiss()

    def update_screen(self, dt):
        try:
            while not self.pbar0.empty():
                sp = self.pbar0.get_nowait()
                if sp != 0:
                    self.root.ids.progressBar1.value += sp
                else:
                    self.root.ids.progressBar1.value = 0
        except Empty:
            pass

        try:
            while not self.pbar1.empty():
                sp = self.pbar1.get_nowait()
                if sp != 0:
                    self.root.ids.progressBar2.value += sp
                else:
                    self.root.ids.progressBar2.value = 0
        except Empty:
            pass

        try:
            while not self.pbar2.empty():
                sp = self.pbar2.get_nowait()
                if sp != 0:
                    self.root.ids.progressBar3.value += sp
                else:
                    self.root.ids.progressBar3.value = 0
        except Empty:
            pass

        try:
            proxysL = len(self.configs['proxys'])
            while not self.totalpb.empty():
                sp = self.totalpb.get_nowait()
                if sp != 0:
                    self.root.ids.totalpb.value += sp
                    comP = (self.root.ids.totalpb.value/proxysL)*100
                    self.root.ids.totalpbText.text = f"{round(comP)}%"
                else:
                    self.root.ids.totalpb.max = proxysL
                    self.root.ids.totalpb.value = 0
        except Empty:
            pass

        self.speedcal()
        self.root.ids.lastScan.text = agoConv(self.selLId).upper()
        self.root.ids.Slist.text = f"list : #{self.selLIdindx}".upper()  # noqa

    def start_scan(self, instance):
        Logger.debug(instance.icon)

        if instance.icon == "play":
            self.listPic()
            if len(self.configs['proxys']) == 0:
                try:
                    if self.configs['proxysInx']:
                        self.tap_target_list_view.start()
                        self.listSel.open()
                        # toast("Pick that list!")
                        return
                except RuntimeError:
                    pass
                PSTDialogInput().open()
                toast("First input proxys ip:port list then start scan.")
                return
            self.configs['proxys'] = dbRW.getAllCurrentProxys(self.selLId)
            self.root.ids.Tproxys.text = f"proxys: {len(self.configs['proxys'])}"  # noqa
            instance.icon = "stop"
            color = "#f44336"
            instance.md_bg_color = get_color_from_hex(color)
            self.theme_cls.primary_palette = "Red"
            if platform == "android":
                self._statusBarColor(color)
                self._wakeScreen(mode="on")
            self.scaning.put_nowait(1)
            self.running.put_nowait(1)

            IndexTime = datetime.now()
            dbRW.updateConfig('proxysInx', IndexTime)
            dbRW.updateProxysInx(IndexTime, self.selLId)
            dbRW.updateProxys(IndexTime, self.selLId)

            configs = dbRW.getAllConfigs()
            self.configs['totalScan'] = dbRW.getProxysInxTS(IndexTime)[0]
            self.root.ids.Tscan.text = f"scan: {self.configs['totalScan']}"
            self.root.ids.plying_spin.active = True
            # print(totalScan)

            self.configs['timeout'] = int(configs[0][3])
            self.configs['fileSize'] = int(configs[0][4])
            self.configs['autoKill'] = int(configs[0][5])
            self.configs['autoKillMode'] = int(configs[0][6])
            self.selLId = str(IndexTime)
            self.show_List()
            self.upScreen = Clock.schedule_interval(self.update_screen, 0.1)

            Logger.debug(f"Proxys : {self.configs['proxys']}")
            Logger.debug(f"Protocol : {self.configs['protocol']}")
            Logger.debug(f"Mirror : {self.configs['mirror']}")

            Thread(target=self.proxySpeedTest, args=(
                self.configs['proxys'],
                self.configs['protocol'],
                self.configs['mirror'],
            )).start()

            # self.proxySpeedTest('start')
        elif instance.icon == "blur":
            toast("Stopping...")
            if self.forceStop.empty():
                self.forceStop.put_nowait(1)
        else:
            while not self.scaning.empty():
                self.scaning.get_nowait()

            if not self.running.empty():
                instance.icon = "blur"
                # instance.text_color
                color = "#9E9E9E"
                self.theme_cls.primary_palette = "Gray"
                instance.md_bg_color = get_color_from_hex(color)
                if platform == "android":
                    self._statusBarColor(color)
                toast(
                    f"Waiting for finish {self.root.ids.currentIP.text[8:]}!")

    def downloadChunk(self, idx, proxy_ip, filename, mirror, protocol):
        Logger.info(f'Scaning {idx} : Started')
        if idx == 0:
            self.root.ids.progressBar1.start()
            self.root.ids.progressBar1.max = 0
        elif idx == 1:
            self.root.ids.progressBar2.start()
            self.root.ids.progressBar2.max = 0
        elif idx == 2:
            self.root.ids.progressBar3.start()
            self.root.ids.progressBar3.max = 0
        try:
            proxies = {
                'http': f'{protocol}://{proxy_ip}',
                'https': f'{protocol}://{proxy_ip}'
            }
            req = get(
                mirror,
                headers={
                    "Range": "bytes=%s-%s" % (0, self.configs['fileSize']),
                    "user-agent": "Mozilla/5.0",
                },
                stream=True,
                proxies=proxies,
                timeout=self.configs['timeout']
            )
            self.showupdate(idx, 'as')
            with(open(f'{filename}{idx}', 'ab')) as f:
                start = datetime.now()
                chunkSize = 0
                # oldSpeed = 0
                chunkSizeUp = 1024
                for chunk in req.iter_content(chunk_size=chunkSizeUp):
                    if not self.forceStop.empty():
                        break
                    end = datetime.now()
                    if 0.1 <= (end-start).seconds:
                        delta = round(
                            float((end - start).seconds) +
                            float(str('0.' + str(
                                (end - start).microseconds))), 3)
                        speed = round((chunkSize) / delta)
                        # if oldSpeed < speed:
                        #     chunkSizeUp *= 3
                        # else:
                        #     chunkSizeUp = speed
                        # oldSpeed = speed
                        start = datetime.now()
                        self.currentSpeed.put_nowait(speed)
                        chunkSize = 0
                    if chunk:
                        chunkSize += sys.getsizeof(chunk)
                        self.showupdate(idx)
                        f.write(chunk)
                if self.configs['autoKillMode']:
                    while not self.forceStop.empty():
                        self.forceStop.get_nowait()
        except ProxyError:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : Could not connect to {proxy_ip}")
            return False
        except connError:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : Could not connect to {proxy_ip}")
            return False
        except IndexError:
            self.showupdate(idx, 'd')
            Logger.info(f'Thread {idx} : You must provide a testing IP:PORT proxy')  # noqa
            return False
        except ConnectTimeout:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : ConnectTimeout for {proxy_ip}")
            return False
        except ReadTimeout:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : ReadTimeout for {proxy_ip}")
            return False
        except RuntimeError:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread {idx} : Set changed size during iteration. {proxy_ip}")  # noqa
            return False
        except KeyboardInterrupt:
            self.showupdate(idx, 'd')
            Logger.info(f"Thread no {idx} : Exited by User.")

        self.showupdate(idx, 'd')

    def showupdate(self, idx, mode='u', error=True):
        if mode == 'u':
            if idx == 0:
                self.pbar0.put_nowait(1)
            elif idx == 1:
                self.pbar1.put_nowait(1)
            elif idx == 2:
                self.pbar2.put_nowait(1)
        elif mode == 'd':
            # color = "#f44336"
            if idx == 0:
                self.pbar0.put_nowait(0)
            elif idx == 1:
                self.pbar1.put_nowait(0)
            elif idx == 2:
                self.pbar2.put_nowait(0)

            self.root.ids.top_text.text = "0 KB/s"
        if mode == 'as' or mode == 'd':
            if idx == 0:
                self.root.ids.progressBar1.stop()
                self.root.ids.progressBar1.max = 1024
                self.root.ids.progressBar1.opacity = 1
            elif idx == 1:
                self.root.ids.progressBar2.stop()
                self.root.ids.progressBar2.max = 1024
                self.root.ids.progressBar2.opacity = 1
            elif idx == 2:
                self.root.ids.progressBar3.stop()
                self.root.ids.progressBar3.max = 1024
                self.root.ids.progressBar3.opacity = 1

    def proxySpeedTest(self, proxys, protocol, mirror):
        filename = 'chunk'
        unsort = list()
        sort = list()
        astTop3 = list()
        roundC = 0
        self.totalpb.put(0)
        Logger.debug(proxys)
        for c, part in enumerate(proxys):
            if self.scaning.empty():
                break
            proxy_ip = part[0].strip()
            self.root.ids.currentIP.text = f"{proxy_ip} <-> {parse.urlparse(self.configs['mirror']).netloc}"  # noqa
            # Removing before test chunk file
            for i in range(3):
                if exists(f'{filename}{i}'):
                    remove(f'{filename}{i}')

            # Starting chunk file downloading
            timeStart = datetime.now()
            downloaders = [
                Thread(
                    target=self.downloadChunk,
                    args=(idx, proxy_ip, filename, mirror, protocol),
                ) for idx in range(3)]
            for _ in downloaders:
                _.start()
            for _ in downloaders:
                _.join()
            timeEnd = datetime.now()

            filesize = 0
            for i in range(3):
                try:
                    filesize = filesize + getsize(f'{filename}{i}')
                except FileNotFoundError:
                    continue

            filesizeM = round(filesize / pow(1024, 2), 2)
            delta = round(
                float((timeEnd - timeStart).seconds) +
                float(str('0.' + str((timeEnd - timeStart).microseconds))), 3)
            speed = round(filesize) / delta

            for i in range(3):
                if exists(f'{filename}{i}'):
                    remove(f'{filename}{i}')

            hotData = {
                'IP': proxy_ip,
                'SIZE': filesizeM,
                'TIME': delta,
                'SPEED': int(speed),
                'top3c': part[6]
            }
            addHistory = [
                hotData,
                self.configs['protocol'],
                self.configs['mirror']]

            unsort.append(hotData)
            sort = self.sort_Type(unsort, showL=False)
            sortLL = len(sort)
            if sortLL >= 3:
                for t in range(sortLL):
                    if t < 3:
                        if sort[t]['SPEED'] != 0:
                            if not sort[t]['IP'] in astTop3:
                                sort[t]['top3c'] += 1
                                astTop3.append(sort[t]['IP'])
                    else:
                        for i in range(len(astTop3)):
                            if sort[t]['IP'] == astTop3[i]:
                                # print(i)
                                astTop3.pop(i)
                                sort[t]['top3c'] -= 1
                                break
            self.show_List(sort)
            self.save_UpdateDB(sort, addHistory)
            self.totalpb.put(1)
            roundC = c
            # return True

        self.root.ids.currentIP.text = "Scan completed"
        self.save_UpdateDB(sort)
        # print(roundC)
        # print(self.root.ids.totalpb.value)
        roundC += 1
        while True:
            if self.root.ids.totalpb.value == roundC:
                self.upScreen.cancel()
                break
        self.root.ids.start_stop.icon = "play"
        self.theme_cls.primary_palette = "LightBlue"
        self.root.ids.start_stop.md_bg_color = self.theme_cls.primary_color
        if platform == "android":
            self._statusBarColor()
            self._wakeScreen(mode="off")
        while not self.running.empty():
            self.running.get_nowait()
        while not self.forceStop.empty():
            self.forceStop.get_nowait()
        self.root.ids.currentIP.text = ""
        self.root.ids.plying_spin.active = False
        Logger.info("Scan : Finished!")

    def sort_Change(self, inst, ckid):
        if not self.data_lists:
            toast("Empty list cannot be sorted.")
        if ckid and inst.active:
            self.sort_Type(self.data_lists, mode=inst.text, reverse=False)
            inst.active = False
        elif ckid and inst.active is False:
            self.sort_Type(self.data_lists, mode=inst.text, reverse=True)
            inst.active = True

    def sort_Type(self, unsort, mode='SPEED', reverse=True, showL=True):
        if mode == 'SERVER':
            mode = 'IP'
        if mode == 'TOP3-%':
            mode = 'top3c'

        sort = sorted(unsort, key=lambda x: x[mode], reverse=reverse)
        if showL:
            self.show_List(sort)
        return sort

    def show_List(self, data=[]):
        # if not self.root.ids.backdrop_front_layer.data:
        # print(data)
        # print(len(self.root.ids.backdrop_front_layer.data))
        totalP = len(self.configs['proxys'])
        ddict = {
            "viewclass": "ProxyShowList",
            "text": "",
            "text1": "",
            "text2": "",
            "text3": "",
            "text4": "",
            "on_release": lambda: toast("Empty !!!")
        }
        if not data:
            self.root.ids.backdrop_front_layer.data = []
            for i in range(25):
                self.root.ids.backdrop_front_layer.data.append(ddict)
        else:
            lenC = len(self.root.ids.backdrop_front_layer.data)
            if lenC < totalP:
                a = totalP - lenC
                for i in range(a):
                    self.root.ids.backdrop_front_layer.data.append(ddict)

            for i in range(totalP):
                try:
                    _ = data[i]
                    self.root.ids.backdrop_front_layer.data[i] = {
                            "viewclass": "ProxyShowList",
                            "text": data[i]['IP'],
                            "text1": f"{round((data[i]['top3c']/self.configs['totalScan'])*100)} %",  # noqa
                            "text2": f"{data[i]['SIZE']} MB",
                            "text3": sec_to_mins(float(data[i]['TIME'])),
                            "text4": f"{size(data[i]['SPEED'], system=alternative)}/s",  # noqa
                            "on_release": lambda x=data[i]['IP']: ProxysDialogHistory(x).open(),  # noqa: E501
                        }
                except IndexError:
                    self.root.ids.backdrop_front_layer.data[i] = ddict

        self.data_lists = data

    def speedcal(self):
        speed = 0
        try:
            while not self.currentSpeed.empty():
                speed += self.currentSpeed.get_nowait()
        except Empty:
            pass

        if speed != 0:
            convS = size(speed, system=alternative)
            if self.configs['autoKillMode']:
                if speed <= self.configs['autoKill']:
                    Logger.debug(f"autoKill : {convS}")
                    self.forceStop.put_nowait(1)
            self.root.ids.top_text.text = f"{convS}/s"  # noqa


if __name__ == "__main__":
    dbRW = MyDb()
    dbRW.create()
    Logger.info(f"App Version: v{__version__}")
    ProxySpeedTestApp().run()
