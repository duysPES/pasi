import pymongo
import datetime
import pysrc.log as log
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

    def _find_one(self, col, criteria):
        try:
            return Bson(self.db[col].find_one(criteria))
        except TypeError:
            return None

    def _insert_one(self, col, bson):
        return self.db[col].insert_one(bson).inserted_id


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
