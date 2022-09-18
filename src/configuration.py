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
    raise ("DATA DIR not found! Please run outside the src folder.")


class Configurator:
    # load every config file at start

    def __init__(self):

        # loads all config

        config_file_names = []
        for config_file_name in os.listdir(CONFIG_DIR_PATH):
            if config_file_name.endswith(".json"):
                config_file_names.append(config_file_name)

        if "default.json" not in config_file_names:
            raise ("default.json not found.")

        config_file_names.remove("default.json")
        self.default_config_json = self._load_config("default.json")

        self.config_json_list = {}

        for config_file_name in config_file_names:
            config_json = self._load_config(config_file_name)
            self.config_json_list[config_file_name.removesuffix(
                ".json")] = merge(self.default_config_json, config_json)

    def get_config(self, pdfname):
        subject_num = self.split_pdfname(pdfname)["subject_num"]
        if subject_num in self.config_json_list.keys():
            return self.config_json_list[subject_num]
        else:
            return self.default_config_json

    @ staticmethod
    def _load_config(config_name):
        config_path = CONFIG_DIR_PATH + config_name
        with open(config_path, "r") as config_file:
            return json.loads(config_file.read())

    @ staticmethod
    def split_pdfname(pdfname):
        """
        input pdfname, return a dict containing each part
        """
        splited = pdfname.split('_')
        return {"subject_num": splited[0],
                "season": splited[1][0], "year": splited[1][1:],
                "type": splited[2], "paper": splited[3][0], "subpaper": splited[3][1]}


CONFIG = Configurator()
