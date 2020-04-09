from pymongo import MongoClient
from bson.objectid import ObjectId   

from demix.config import get_cfg

cfg = get_cfg('mongo')

def get_db():
    client = MongoClient(cfg['db_url']).recipedb
    return client