
from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label



class QuestionScreen(ModalScreen):
    CSS_PATH = "style.tcss"


    def __init__(self, question, yes, no):
        super().__init__()
        self.question = question
        self.yes = yes
        self.no = no


    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.question, id="question"),
            Button(self.yes["text"], variant=self.yes["variant"], id="yes"),
            Button(self.no["text"], variant=self.no["variant"], id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.yes["call"]()
        if event.button.id == "no":
            self.no["call"]()

        self.app.pop_screen()


