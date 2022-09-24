import os
import json
from jsonmerge import merge

ROOT_DIR_PATH = os.getcwd() + "/"
DATA_DIR_PATH = ROOT_DIR_PATH + "data/"
CONFIG_DIR_PATH = ROOT_DIR_PATH + "config/"
DEBUG_DIR_PATH = ROOT_DIR_PATH + "debug/"
TMP_DIR_PATH = ROOT_DIR_PATH + "tmp/"

# detect if path is right
if not os.path.exists(DATA_DIR_PATH):
    raise ("data dir not found")
