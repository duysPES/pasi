from pysrc.config import Config
import pysrc.log as log
import pprint
import pymongo

db = pymongo.MongoClient("localhost", 27017)['db']
db.jobs.create_index([('name', pymongo.ASCENDING)], unique=True)
pp = pprint.PrettyPrinter(indent=4)


def log_gui(msg, status='info'):
    """
    ```python
    input: str
    return: None
    ```
    Wrapper around log object to verify that output from GUI is going to gui.log
    """
    log.log(status)(msg, log.LogType.gui)


config = Config()
