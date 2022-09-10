import configparser
from os.path import exists

CONFIG_PATH = "config/config.ini"
CONFIG = configparser.ConfigParser()

if not exists(CONFIG_PATH):

    # default config begins here

    # global config
    CONFIG["global"]["db_path"] = "data/db.sqlite"

    # default config ends here

    CONFIG.write(CONFIG_PATH)

else:
    CONFIG.read(CONFIG_PATH)
