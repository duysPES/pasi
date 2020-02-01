import pymongo
import datetime
import pathlib
import configparser
import pysrc.log as log
import pprint
import json
from pysrc.job import Job, Pass
from pysrc.bson import Bson


class Database:
    ATTACH_JOB_CRITERIA = {'_id': 0}

    def __init__(self):
        self.db = pymongo.MongoClient("localhost", 27017)['db']
        self.db.jobs.create_index([('name', pymongo.ASCENDING)], unique=True)

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
        return self.db[col].update_one(filter=filter,
                                       update=update_query,
                                       upsert=upsert).matched_count

    def _find_all_records(self, col):
        return self.db[col].find()

    def _find_one(self, col, criteria={}, **kwargs):
        try:
            return Bson(self.db[col].find_one(filter=criteria, **kwargs))
        except TypeError:
            return None

    def _insert_one(self, col, bson):
        return self.db[col].insert_one(bson).inserted_id


class ConfigDB(Database):
    def __init__(self):
        super(ConfigDB, self).__init__()
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
        print('pasi', 'theme', theme_value)
        self.update('pasi', 'theme', theme_value.lower())

    def lisc(self, section):
        return self.get("lisc", section)

    def switches(self, section):
        return self.get("switches", section)

    def pasi(self, section):
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
        with open(self.ini, 'r') as f:
            d = eval(f.read())
            return d

    def write_ini(self):
        settings = self._find_all_records("config")[0]
        with open(self.ini, 'w') as f:
            f.write(json.dumps(settings, indent=4, sort_keys=True))


class JobHandler(Database):
    def update_jobs(self, filter, update_query):
        return self._update("jobs",
                            filter=filter,
                            update_query=update_query,
                            upsert=False)

    def find_job(self, job_name):
        bson = self._find_one("jobs", {"name": job_name})
        return Job(**bson)

    def find_job_by_id(self, job_id):
        bson = self._find_one("jobs", {"_id": job_id})
        return Job(**bson)

    def add_job(self, bson):
        if not isinstance(bson, Bson):
            raise ValueError(f"{type(bson)} is not of type Bson")

        self._insert_one("jobs", bson)

    def all_jobs(self):
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
