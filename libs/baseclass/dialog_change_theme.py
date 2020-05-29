import os

from kivy.uix.modalview import ModalView

from kivy.utils import get_color_from_hex, get_hex_from_color

from kivymd.color_definitions import palette, colors
from kivymd.theming import ThemableBehavior
import re
from kivymd.toast import toast


class KitchenSinkBaseDialog(ThemableBehavior, ModalView):
    pass


class KitchenSinkDialogDev(KitchenSinkBaseDialog):
    pass

class PSTDialogInput(KitchenSinkBaseDialog):
    def __init__(self, **kwargs):
        super(PSTDialogInput, self).__init__(**kwargs)
        self.filename = 'proxys.txt'

        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding="utf-8") as r:
                self.ids.query.text = r.read()
    
    def inputedproxysSave(self):
        proxys = re.findall(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}[\s:\t][0-9]{1,5}",
        self.ids.query.text)
        for line in range(len(proxys)):
            proxys[line] = re.sub(r'[\s]', ':', proxys[line])
        
        currentSave = ""
        for line in proxys:
            currentSave += line+'\n'

        with open(self.filename, 'w', encoding="utf-8") as r:
            r.write(currentSave)
            
        self.ids.query.text = currentSave
        
        toast(f"Saved!", duration=0.7)


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
