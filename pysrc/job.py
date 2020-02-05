import pprint
from pysrc.bson import Bson


class Pass:
    @classmethod
    def deserialize(cls, **kwargs):
        """
        deconstruct a dictionary to instance of a pass
        """
        return cls(kwargs['num'], kwargs['job'])

    def __init__(self, pass_number: int, job_id: int):
        self.num = pass_number
        self.job_id = job_id

    def __str__(self):
        return f"< Pass: {self.num} >"

    def prettify(self):
        pp = pprint.PrettyPrinter(indent=4)
        return pp.pformat(self.serialize())

    def serialize(self):
        """
        take contents of Pass and serialize into bson object for consumption to mongo
        """
        serial: Bson = Bson({
            "job":
            self.job_id,
            "num":
            self.num,
            "name":
            str(self),
            "logs":
            "This is an example log, replace this will output from lisc"
        })
        return serial


class Job:
    def __init__(self, *args, **kwargs):
        self.__dict__ = kwargs

        must_haves = ['_id', 'name']
        for must_have in must_haves:
            if must_have not in self.__dict__:
                raise NotImplementedError(
                    "Job must consist of at least a name and id")

    def add_pass(self, new_pass: Pass, make_active=True):
        self.__dict__["passes"].append(new_pass.serialize())
        if make_active:
            self.active_pass = new_pass

    def set_active_pass(self, p: Pass):
        self.active_pass = p

    def clear_active_pass(self):
        self.active_pass = None

    def get_pass(self, name: str):
        pass_objs = self.pass_objs()

        for p in pass_objs:
            if str(p) == name:
                return p
        return None

    def pass_objs(self):
        # return [p['name'] for p in self.__dict__['passes']]
        return [Pass.deserialize(**p) for p in self.__dict__['passes']]

    def for_win_title(self, p=None):
        x = f":{str(p)}" if p is not None else ""
        return f"< {self.name}:{self.client}{x} >"

    def keys(self):
        return self.__dict__.keys()

    def items(self):
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
