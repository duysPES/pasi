# from pysrc.config import Config

from pysrc.db import JobHandler, ConfigDB
import pysrc.log as log
import pprint
import pymongo

config: ConfigDB = ConfigDB()
# config = Config()
db: JobHandler = JobHandler()


def log_gui(msg, status='info'):
    """
    ```python
    input: str
    return: None
    ```
    Wrapper around log object to verify that output from GUI is going to gui.log
    """
    log.log(status)(msg, log.LogType.gui)
