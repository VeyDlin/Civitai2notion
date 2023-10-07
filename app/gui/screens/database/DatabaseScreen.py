from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Button, RichLog, LoadingIndicator
from textual.containers import Horizontal

from ....util.Log import Log
from ....util.Worker import Worker
from ..popup.PopupScreen import PopupScreen
from ..question.QuestionScreen import QuestionScreen


class DatabaseScreen(Screen):
    CSS_PATH = "style.tcss"


    def compose(self) -> ComposeResult:
        yield Horizontal(
            Button("Import from civitai", id="ipmport", variant="success"),
            Button("Download from notion", id="download", variant="warning"),
            Button("Update notion database", id="update", variant="warning"),
            Button("Make all", id="make-all", variant="primary"),
            LoadingIndicator(id="load"),
            id="top-content"
        )
        yield RichLog(wrap=True, markup=True, id="log")
        
        yield Footer()



    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if Worker.busy():
            self.app.push_screen(PopupScreen("The action is not possible until all processes are finished"))
            return
        
        id = event.button.id
        self.query_one("#load").styles.display = "block"
        
        if id == "ipmport":
            self.run_worker(Worker.ipmport_models_from_favorites(), exclusive=True) 
        if id == "download":
            self.app.push_screen(QuestionScreen(
                "How do you want to download files from the database?",
                {
                    "text": "Just download",
                    "variant": "primary",
                    "call": lambda: self.run_worker(Worker.download_models_from_notion_database(hash_check=False), exclusive=True)   
                },
                {
                    "text": "Download with hash check",
                    "variant": "warning",
                    "call": lambda: self.run_worker(Worker.download_models_from_notion_database(hash_check=True), exclusive=True)   
                }
            ))
        if id == "update":
            self.run_worker(Worker.update_notion_database(), exclusive=True)
        if id == "make-all":
            self.app.push_screen(QuestionScreen(
                "When the action reaches the file download stage, how do you want to download files from the database?",
                {
                    "text": "Just download",
                    "variant": "primary",
                    "call": lambda: self.run_worker(Worker.make_all(False), exclusive=True)
                },
                {
                    "text": "Download with hash check",
                    "variant": "warning",
                    "call": lambda: self.run_worker(Worker.make_all(True), exclusive=True)
                }
            ))
   


    def on_mount(self):
        Worker.set_end_work_call(self.end_work)
        Log.set_call(self.write_log)



    def end_work(self):
        self.query_one("#load").styles.display = "none"



    def write_log(self, type, name, text):
        color = None
        if type == Log.INFO:
            color = "while"
        if type == Log.OK:
            color = "green"
        if type == Log.WARNING:
            color = "yellow"
        if type == Log.ERROR:
            color = "red"

        log = self.query_one(RichLog)

        if name is None:
            log.write(f"[bold {color}]{text}[/]")
        else:
            log.write(f"[bold {color}][{name.upper()}][/] {text}")