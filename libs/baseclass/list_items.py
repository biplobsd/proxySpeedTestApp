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
