from app.gui.MainApp import MainApp
from app.util.Config import Config



if __name__ == "__main__":
    Config.init("config.user.json", "config.temp.json")

    app = MainApp()
    app.run()
    import sys

    sys.exit(app.return_code or 0)