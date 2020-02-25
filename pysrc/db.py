"""
Holds all logic that handles with communication and interaction with
MongoDB. 
"""

import pymongo
import datetime
import pathlib
import configparser
import pysrc.log as log
import pprint
import json
from pysrc.job import Job, Pass
from pysrc.bson import Bson

_DB = pymongo.MongoClient("localhost", 27017)['db']


class Database:
    """
    Base class that represents the handle to mongodb
    """
    ATTACH_JOB_CRITERIA = {'_id': 0}

    def __init__(self, *args, **kwargs):
        self.db = _DB
        self.db.jobs.create_index([('name', pymongo.ASCENDING)], unique=True)
        self.db.logs.create_index([('job_id', pymongo.ASCENDING)], unique=True)

        # create a single uid instance of attach

        self._update(col='attach',
                     filter=self.ATTACH_JOB_CRITERIA,
                     update_query={"$set": {
                         'job': None
                     }},
                     upsert=True)

    def log(self, msg, status='info'):
        log.log(status)(msg, log.LogType.gui)

    def _update(self, col, filter, update_query, upsert=False):
        """
        helper wrapper that updates a single record within the mongo
        by suppling collection, filter, and update_query. Upsert is False
        by default
        """
        return self.db[col].update_one(filter=filter,
                                       update=update_query,
                                       upsert=upsert).matched_count

    def _find_all_records(self, col):
        """
        returns all records within a specified collection
        """
        return self.db[col].find()

    def _find_one(self, col, criteria={}, **kwargs):
        """
        returns a single record in mongo based on criteria from supplied
        collection.
        """
        try:
            return Bson(self.db[col].find_one(filter=criteria, **kwargs))
        except TypeError:
            return None

    def _insert_one(self, col, bson):
        """
        inserts a single record in mongo based on supplied args
        returns the UID of created record.
        """
        return self.db[col].insert_one(bson).inserted_id


class Log(Database):
    """
    Sub-Class that connnects to database representing the Logging module. 
    Logging logic is as follows:

    Each Job that is created as associated Passes. Each pass holds it individual logs.
    """
    EMPTY_LOG = {"contents": [], "job_id": None, "pass_name": None}
    _id = None
    _raw = None
    cur_pass = None

    @classmethod
    def get_contents(cls, p: Pass) -> str:
        """
        supply a pass, and obtain the contents of said pass, if it
        exists within database
        """

        log = cls(p)
        key = str(p.num)
        try:
            return "".join(log._raw['contents'][key])
        except Exception:
            return ""

    def __init__(self, p: Pass):

        # check to see if pass.job_id exists within Logs
        self.db = _DB
        self.cur_pass = p
        self._raw = self._find_one("logs", {"job_id": p.job_id})

        if self._raw is None:
            # create empty record for log and associate the job_id with it.
            init = {"job_id": p.job_id, "contents": {}}
            self._id = self._insert_one("logs",
                                        bson=init)  # this returns Log._id
        else:
            # set class id and raw obj to log object found in database
            self._id = self._raw['_id']
            self._raw = self._find_one("logs", {"_id": self._id})

    def log(self, msg, status):
        """
        log a string of certain status and attach to log object.
        """

        # can not log to a specific log object if _id is not known.
        if self._id is None:
            raise AttributeError(
                "can only invoke method within context manager")

        # format the args
        now = datetime.datetime.now().ctime()
        log_msg = "{}: {} [{}]\n".format(now, status.upper(), msg)

        # construct the update_query using Log._id
        filter = {"_id": self._id}
        update_query = {"$push": {f"contents.{self.cur_pass.num}": log_msg}}

        # physically append logging msg to appropriate list within log object.
        self._update("logs",
                     filter=filter,
                     update_query=update_query,
                     upsert=True)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self._id = None
        self._raw = None


class ConfigDB(Database):
    """
    global configuration settings utilizing mongo backend

    """
    def __init__(self):
        # super(ConfigDB, self).__init__(reset_attach=False)
        # self.db = pymongo.MongoClient("localhost", 27017)['db']
        self.db = _DB
        self.ini = (pathlib.Path(__file__).parent.parent /
                    "config.json").resolve()
        # set default config files, with collection: 'config'
        bson = self.read_ini()
        self._update("config",
                     filter={"_id": 0},
                     update_query={"$set": bson},
                     upsert=True)

        self.update("pasi", "height", "900")

    def update_theme(self, theme_value):
        """
        change theme in configuration settings
        """
        self.update('pasi', 'theme', theme_value.lower())

    def lisc(self, section):
        """
        return values from lisc header
        """
        return self.get("lisc", section)

    def switches(self, section):
        """
        return values from switches header
        """
        return self.get("switches", section)

    def pasi(self, section):
        """
        return values from PASI header
        """
        return self.get("pasi", section)

    def get(self, header, section):
        """
        retrieve value from header and section
        """
        setting = self._find_one("config",
                                 projection={f"{header}.{section}": 1})
        return setting[header][section]

    def update(self, header, section, value):
        """
        update a header and section with a value
        """
        update_query = {"$set": {f"{header}.{section}": value}}
        match = self._update("config",
                             filter={"_id": 0},
                             update_query=update_query,
                             upsert=False)

    def read_ini(self):
        """
        read flat files json configuration file and
        populate mongo with values
        """
        with open(self.ini, 'r') as f:
            d = eval(f.read())
            return d

    def write_ini(self):
        """
        dump configuration settings from mongo
        to json file
        """
        settings = self._find_all_records("config")[0]
        with open(self.ini, 'w') as f:
            f.write(json.dumps(settings, indent=4, sort_keys=True))


class JobHandler(Database):
    """
    handler to database used for
    manipulation of Jobs in Job Planner and Shooting interface.
    """
    def update_jobs(self, filter, update_query):
        """
        update a specific job with associated filter and update_query
        """
        return self._update("jobs",
                            filter=filter,
                            update_query=update_query,
                            upsert=False)

    def find_job(self, job_name):
        """
        find a job in the database based on name and convert to Job object
        """
        bson = self._find_one("jobs", {"name": job_name})
        return Job(**bson) if bson is not None else None

    def find_job_by_id(self, job_id):
        """
        find a job by job_id and convert to Job object
        """
        bson = self._find_one("jobs", {"_id": job_id})
        return Job(**bson) if bson is not None else None

    def add_job(self, bson):
        """
        add a job based on bson representation of job.
        TODO: change the incoming parameter to use job: Job and not bson: Bson
        """
        if not isinstance(bson, Bson):
            raise ValueError(f"{type(bson)} is not of type Bson")

        self._insert_one("jobs", bson)

    def all_jobs(self):
        """
        returns all job records in database.
        In a format of 

        ```python
        jobs = {
            'job_name': <Object: Job>
        }
        ```
        """
        all_jobs = self._find_all_records('jobs')
        jobs = {}
        for job in all_jobs:
            jobs[job['name']] = Job(**job)

        return Bson(jobs)

    def attach_job(self, name):
        """
        finds job in db, and sets a single record
        in db.attach to point to UID of job that is attached
        """
        job = self.find_job(name)
        if job is None:
            return False

        uid = job.id
        self._update('attach',
                     filter=self.ATTACH_JOB_CRITERIA,
                     update_query={"$set": {
                         "job": uid
                     }})
        return True

    def detach_job(self):
        """
        simply set the attached job flag in db to null
        """
        # set currently attached jobs - active pass to null

        self._update('attach',
                     filter=self.ATTACH_JOB_CRITERIA,
                     update_query={"$set": {
                         "job": None
                     }})

    def attached_job(self):
        """
        return the attached job for shooting panel
        """
        uid = self._find_one('attach',
                             criteria=self.ATTACH_JOB_CRITERIA)['job']

        bson = self._find_one('jobs', criteria={"_id": uid})

        try:
            return Job(**bson)
        except TypeError:
            return None

    def active_pass(self):
        """
        returns the pass number for attached job
        """

        job: Job = self.attached_job()
        return Pass(job.active_pass, job.id)

    def activate_pass(self, p: Pass):
        """
        Change the 'active_pass' field for specific job
        that is tied to Pass in arg
        """

        job = self.find_job_by_id(p.job_id)

        result = False
        for jp in job.pass_objs():
            if jp.num == p.num:
                result = True
                break
        if not result:
            raise IndexError("trying to activate a pass that doesn't exist")

        matched_count = self.update_jobs(
            filter={"name": job.name},
            update_query={"$set": {
                "active_pass": p.num
            }})

    def add_pass(self, p: Pass, make_active=False):
        """
        append selected pass to specific job
        """
        job = self.find_job_by_id(p.job_id)
        job.add_pass(p)

        activate = p.num if make_active else None
        print("Make active is: ", make_active, " ", activate)

        matched_count = self.update_jobs(filter={"name": job.name},
                                         update_query={
                                             "$set": {
                                                 "passes": job.passes,
                                                 "active_pass": activate
                                             }
                                         })
