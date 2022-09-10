import configparser
import os

ROOT_DIR_PATH = os.getcwd() + "/"
DATA_DIR_PATH = ROOT_DIR_PATH + "data/"
CONFIG_DIR_PATH = ROOT_DIR_PATH + "config/"
DEBUG_DIR_PATH = ROOT_DIR_PATH + "debug/"

GLOBAL_CONFIG_FILE_PATH = CONFIG_DIR_PATH + "config.ini"
GLOBAL_CONFIG = configparser.ConfigParser()

if not os.path.exists(GLOBAL_CONFIG_FILE_PATH):

    # default config begins here

    # default config ends here

    GLOBAL_CONFIG.write(GLOBAL_CONFIG_FILE_PATH)

else:
    GLOBAL_CONFIG.read(GLOBAL_CONFIG_FILE_PATH)
