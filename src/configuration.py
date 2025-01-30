import os
import json
from jsonmerge import merge

ROOT_DIR_PATH = os.getcwd() + "/"
DATA_DIR_PATH = ROOT_DIR_PATH + "data/"
CONFIG_DIR_PATH = ROOT_DIR_PATH + "config/"
DEBUG_DIR_PATH = ROOT_DIR_PATH + "debug/"
TMP_DIR_PATH = ROOT_DIR_PATH + "tmp/"


# TODO: remove this
os.system("mkdir -p data/pdf")
os.system("mkdir -p data/cached_image")
os.system("mkdir -p data/cached_pdf")
os.system("mkdir -p debug/json")
os.system("mkdir -p debug/pdf")

# detect if path is right
if not os.path.exists(DATA_DIR_PATH):
    raise Exception("data dir not found")
