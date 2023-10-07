from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Markdown
import os



class HelpScreen(Screen):
    CSS_PATH = "style.tcss"

    def compose(self) -> ComposeResult:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file = open(os.path.join(current_dir, "help.md"), "r")
        help = file.read()
        file.close()

        yield Markdown(help)
        yield Footer()