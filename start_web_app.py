from modules.KanjiWebApp import KanjiWebApp
from modules.Config import Config
import os


if __name__ == '__main__':
    base_dir = os.path.dirname(__file__)
    config = Config(os.path.join(base_dir, 'config.ini'))
    app = KanjiWebApp(config)
    app.run()
