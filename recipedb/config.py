import configparser
import os
from recipedb.utils.directory import current_directory

CONFIG = current_directory(__file__) + "/recipedb.cfg"

def get_cfg(section):
    config = configparser.ConfigParser()
    config.read(CONFIG)
    api = config.items(section)
    return dict(api)