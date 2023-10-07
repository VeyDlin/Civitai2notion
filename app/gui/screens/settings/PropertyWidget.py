from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label, Input, Switch
from ....util.Config import Config


class TimeDisplay(Static):
    """A widget to display elapsed time."""


class PropertyWidget(Static):
    def __init__(self, prop):
        super().__init__()
        self.prop = prop
        self.prop_path = prop.path
        self.control = None


    def compose(self) -> ComposeResult:
        yield Label(self.prop.title)

        if self.prop.type == "password":
            self.control = Input(password=True, value=str(self.prop.data), placeholder=self.prop.hint)
        if self.prop.type == "string":
            self.control = Input(password=False, value=str(self.prop.data), placeholder=self.prop.hint)
        if self.prop.type == "bool":
            self.control = Switch(animate=False, value=bool(self.prop.data))
        if self.prop.type == "path":
            self.control = Input(password=False, value=str(self.prop.data), placeholder=self.prop.hint)

        yield Horizontal(self.control, classes="right-dock")



    def update_value(self):
        if self.prop.type == "bool":
            self.control.value = bool(Config.get(self.prop_path).data)
        else:
            self.control.value = str(Config.get(self.prop_path).data)



    def set_value(self):
        if self.prop.type == "bool":
            Config.get(self.prop_path).data = bool(self.control.value)
        else:
            Config.get(self.prop_path).data = str(self.control.value)