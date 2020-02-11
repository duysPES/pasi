import pprint
from pysrc.bson import Bson
from typing import *


class Pass:
    """
    Represents a Pass and hold information about Inventory logging messages, switches found, successfull/errored fires 
    etc...
    """
    __Log: str = ""

    @classmethod
    def deserialize(cls, **kwargs):
        """
        deconstruct a dictionary to instance of a pass
        """
        c = cls(kwargs['num'], kwargs['job'])
        c.add_log(kwargs['logs'])
        return c

    def serialize(self):
        """
        take contents of Pass and serialize into bson object for consumption to mongo
        """
        serial: Bson = Bson({
            "job": self.job_id,
            "num": self.num,
            "name": str(self),
            "logs": self.__Log
        })
        return serial

    def __init__(self, pass_number: int, job_id: int):
        self.num = pass_number
        self.job_id = job_id

    def __str__(self):
        return f"< Pass: {self.num} >"

    def add_log(self, log: str, append=False):
        """
        adds a log to Pass
        has capabilities to append as well
        """
        if not append:
            self.__Log = log
        else:
            self.__Log = f"{self.__Log}{log}"

    def prettify(self):
        """
        returns a 'pretty' version of a serialized Pass
        """
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(self.serialize())

    def summary(self):
        """
        used for headers and prints. Shows the name and contents of Log
        """
        string = f"{str(self)}\nLogs\n{self.__Log}"
        return string


class Job:
    """
    Abstraction representation of a Job. A job can have one or more Passes, each 
    with their own information and metadata. 
    """
    def __init__(self, *args, **kwargs):
        """
        Supplies a dict-style argument and dynamically 
        creates attributes from the dict. Must have _id and name in the
        keys for it to be valid dict
        """
        self.__dict__ = kwargs

        must_haves = ['_id', 'name']
        for must_have in must_haves:
            if must_have not in self.__dict__:
                raise NotImplementedError(
                    "Job must consist of at least a name and id")

    def add_pass(self, new_pass: Pass, make_active=True):
        """
        Append to list of passes, serialized
        """
        self.__dict__["passes"].append(new_pass.serialize())
        if make_active:
            self.active_pass = new_pass

    def get_active_pass(self) -> Pass:
        """
        return the Pass object for jobs internal active pass
        """
        return self.get_pass_by_num(self.active_pass)

    def get_pass_by_num(self, num: int) -> Pass:
        """
        get Pass object by supplied pass_number
        """
        for pass_obj in self.pass_objs():
            if pass_obj.num == num:
                return pass_obj
        raise IndexError(
            f"Attempting to retrieve Pass that doesn't exist in job: {self._id}"
        )

    def get_pass_by_name(self, pass_name: str) -> Pass:
        """
        get Pass object by supplied pass name
        """
        pass_objs = self.pass_objs()

        for p in pass_objs:
            if str(p) == name:
                return p
        return None

    def pass_objs(self) -> List[Pass]:
        """
        return the list of Pass Objects
        """
        # return [p['name'] for p in self.__dict__['passes']]
        return [Pass.deserialize(**p) for p in self.__dict__['passes']]

    def for_win_title(self, p: Pass):
        """
        Format current job for window title
        """
        x = f":Pass[{p.num}]" if p is not None else ""
        return f"< {self.name}:{self.client}{x} >"

    def keys(self):
        """
        return intenal keys of __dict__
        """
        return self.__dict__.keys()

    def items(self):
        """
        return internal values of __dict__
        """
        return self.__dict__.items()

    @property
    def id(self):
        return self.__dict__['_id']

    @property
    def d(self):
        return self.__dict__

    def __str__(self):
        pp = pprint.PrettyPrinter(indent=4)
        fmt = pp.pformat(self.__dict__)
        return fmt
