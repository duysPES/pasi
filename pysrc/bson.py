from typing import *
import datetime


class Bson(dict):
    def __init__(self, *args):
        super(Bson, self).__init__(*args)

    def clean_bson(self):
        bson = self
        tmp = bson.copy()
        for key, val in tmp.items():
            if isinstance(val, str):
                bson[key] = val.strip()
        return self

    def add_date(self):
        self['date'] = str(datetime.datetime.now())
        return self

    def add_field(self, key, value):
        self[key] = value
        return self