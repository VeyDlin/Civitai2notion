
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label



class PopupScreen(ModalScreen):
    CSS_PATH = "style.tcss"


    def __init__(self, text):
        super().__init__()
        self.text = text


    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.text, id="info"),
            Button("Okay", variant="primary", id="okay"),
            id="dialog"
        )



    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "okay":
            self.app.pop_screen()