from textual.app import App

from .screens.database.DatabaseScreen import DatabaseScreen
from .screens.settings.SettingsScreen import SettingsScreen
from .screens.help.HelpScreen import HelpScreen


class MainApp(App[str]):
    BINDINGS = [
        ("d", "switch_mode('database')", "Database"),  
        ("s", "switch_mode('settings')", "Settings"),
        ("h", "switch_mode('help')", "Help"),
    ]
    MODES = {
        "database": DatabaseScreen,
        "settings": SettingsScreen,
        "help": HelpScreen
    }

    def on_mount(self) -> None:
        self.switch_mode("database")  
