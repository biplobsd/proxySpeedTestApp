from hurry.filesize.filesize import size, alternative
from kivymd.uix.taptargetview import MDTapTargetView
from libs.baseclass.utils import agoConv, sec_to_mins
from kivy.uix.modalview import ModalView
from kivymd.theming import ThemableBehavior
from libs.baseclass.database import MyDb
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.widget import Widget

from kivymd.uix.list import (
    OneLineAvatarListItem,
    ILeftBody,
    TwoLineAvatarListItem,
    IRightBodyTouch,
    OneLineIconListItem,
    OneLineListItem
)
from kivymd.uix.selectioncontrol import MDCheckbox


class KitchenSinkOneLineLeftAvatarItem(OneLineAvatarListItem):
    divider = None
    source = StringProperty()


class pSTOneLineListItem(OneLineListItem):
    divider = 'Insert'


class MenuOneLineListItem(OneLineListItem):
    divider = 'Full'
    _txt_bot_pad = dp(10)
    font_style = "Caption"


class KitchenSinkTwoLineLeftAvatarItem(TwoLineAvatarListItem):
    icon = StringProperty()
    secondary_font_style = "Caption"


class KitchenSinkTwoLineLeftIconItem(TwoLineAvatarListItem):
    icon = StringProperty()


class KitchenSinkOneLineLeftIconItem(OneLineAvatarListItem):
    icon = StringProperty()


class KitchenSinkOneLineIconListItem(OneLineIconListItem):
    icon = StringProperty()


class KitchenSinkOneLineLeftWidgetItem(OneLineAvatarListItem):
    color = ListProperty()


class LeftWidget(ILeftBody, Widget):
    pass


class IconRightSampleWidget(IRightBodyTouch, MDCheckbox):
    pass


class ProxysDialogHistory(ThemableBehavior, ModalView):
    def __init__(self, ipaddr="", **kwargs):
        super().__init__(**kwargs)
        self.dbRW = MyDb()
        self.ipaddr = ipaddr
        self.ids.ip.text, \
            self.ids.port.text = ipaddr.split(":")
        addrScnHist = self.dbRW.getAllProxyScan(ipaddr)
        from main import ProxyShowList

        for i, p in enumerate(addrScnHist):
            self.ids.md_list.add_widget(ProxyShowList(
                text=f"{agoConv(p[5])}",
                text1=f"{p[4]}",
                text2=f" {size(p[3], system=alternative)}/s",
                text3=f" {p[1]} MB",
                text4=f" {sec_to_mins(float((p[2])))}",
                _height=dp(20)
            ))
        if self.dbRW.getConfig("openNo")[0] == 1:
            fulladdrCopyTT = MDTapTargetView(
                widget=self.ids.adds,
                title_text="Copy full IP:PORT by tapping ':' semicolon symbol",
                description_text="That's way you can copy full address faster way.",
                widget_position="bottom",
                outer_radius=dp(250)
            )
            fulladdrCopyTT.bind(
                on_open=lambda x: self.textColorChange('o'),
                on_close=lambda x: self.textColorChange('c')
            )
            fulladdrCopyTT.start()

    def textColorChange(self, m='o'):
        if m == 'o':
            self.ids.adds.theme_text_color = "Custom"
            self.ids.ip.text_color = self.theme_cls.primary_light
            self.ids.port.text_color = self.theme_cls.primary_light
            self.ids.ip.disabled = True
            self.ids.port.disabled = True
        elif m == 'c':
            self.ids.adds.theme_text_color = "Hint"
            self.ids.ip.text_color = self.theme_cls.primary_light
            self.ids.port.text_color = self.theme_cls.primary_light
            self.ids.ip.disabled = False
            self.ids.port.disabled = False
