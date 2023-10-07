from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.widgets import Footer, Collapsible, Button

from .PropertyWidget import PropertyWidget
from ..popup.PopupScreen import PopupScreen
from ....util.Config import Config
from ....util.Worker import Worker


class SettingsScreen(Screen):
    CSS_PATH = "style.tcss"
    properties = []


    def compose(self) -> ComposeResult:
        ettings_content = VerticalScroll(id="settings-content")

        for group in Config.groups:

            collapsible = Collapsible(title=group.title)
            group_content = Vertical(id="group-content")

            for prop in group.properties:
                property = PropertyWidget(prop)
                self.properties.append(property)
                group_content.compose_add_child(property)

            collapsible.compose_add_child(group_content)
            ettings_content.compose_add_child(collapsible)


        ettings_content.compose_add_child(Horizontal(
            Button("Reset", id="reset", variant="warning"),
            Button("Save", id="save", variant="success"),
            id="save-content"
        ))

        yield ettings_content

        yield Footer()


    def on_mount(self) -> None:
        pass 


    def on_button_pressed(self, event: Button.Pressed) -> None:
        id = event.button.id
        if id == "save":
            self.save_config()
        if id == "reset":
            self.reset_config()



    def save_config(self):
        if Worker.busy():
            self.app.push_screen(PopupScreen("The action is not possible until all processes are finished"))
            return
        
        for prop in self.properties:
            prop.set_value()
        Config.save()



    def reset_config(self):
        Config.reset()
        for prop in self.properties:
            prop.update_value()
