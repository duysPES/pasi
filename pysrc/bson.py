"""
A wrapper around python native Dict object, that supports Mongos native storage type
which is BSON
"""

from typing import *
import datetime


class Bson(dict):
    """
    class that represents mongos native storage type
    """
    def __init__(self, *args):
        super(Bson, self).__init__(*args)

    def clean_bson(self):
        """
        cleans up all entries of key:value stripping away newlines and whitespace
        """
        bson = self
        tmp = bson.copy()
        for key, val in tmp.items():
            if isinstance(val, str):
                bson[key] = val.strip()
        return self

    def add_date(self):
        """
        appends current time to internal key:value and/or overwrites
        key if it exists. 
        """
        # self['date'] = str(datetime.datetime.now())
        self.add_field('date', str(datetime.datetime.now()))
        return self

    def add_field(self, key, value):
        """
        a wrapper around creating a key:value pair
        """
        self[key] = value
        return self