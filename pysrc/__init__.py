from pysrc.config import Config
import pysrc.db
import pysrc.log as log
import pprint
import pymongo

db = pysrc.db.JobHandler()


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
