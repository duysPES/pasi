import pymongo
import PySimpleGUI as sg
import datetime
from pysrc import db, config, pp
from pysrc.layout import MainWindowLayout


class JobPlanner:
    @staticmethod
    def check_element(values, key, invalid=''):
        if values[key].strip() == invalid:
            return False
        return True

    @staticmethod
    def form_ok(values, ignore=[]):
        """
        check form to see if it okay. returns a list of invalid element names
        """
        tmp_values = values.copy()

        JobPlanner.remove_from_values(tmp_values, to_remove=ignore)

        invalid = []

        for name in tmp_values.keys():
            if not JobPlanner.check_element(tmp_values, name):
                invalid.append(name)

        if len(invalid) > 0:
            string = ""
            for x in invalid:
                string += f"You must supply a value for `{x}`\n"
            sg.PopupError(string, title="ERROR", keep_on_top=True)
            return False

        return True

    @staticmethod
    def remove_from_values(values, to_remove):
        """
        remove elements from values that are not part of form
        if elements in `to_remove` contains a '!'  it will ignore everything  EXCEPT
        the !, can not mix ! and normal, if it detects a ! it will ignore all besides elements with !
        """
        to_keep = []
        for x in to_remove:
            if '!' in x:
                to_keep.append(x.replace("!", ""))

        if len(to_keep) == 0:
            for x in to_remove:
                del values[x]
        else:
            tmp_values = values.copy()
            for key in tmp_values.keys():
                if key not in to_keep:
                    del values[key]

    @staticmethod
    def clean_bson(bson):
        """
        do pre-processing on values in bson
        """

        # removes all white space and newlines

        print(bson)
        tmp = bson.copy()
        for key, val in tmp.items():
            if isinstance(val, str):
                bson[key] = val.strip()

    @staticmethod
    def add_date(bson):
        """
        Since date is saved as a label, it is not included 
        in events, and values. This simply takes current time and adds to bson object
        """

        bson['date'] = str(datetime.datetime.now())


class JobPlannerSave(JobPlanner):
    @staticmethod
    def run(win, event, values):
        # first check to see if any of the fields are empty
        if JobPlanner.form_ok(values, ignore=["main_menu", "passes"]):
            # form is okay, construct bson document
            bson = values.copy()
            JobPlanner.remove_from_values(bson, to_remove=["main_menu"])
            JobPlanner.clean_bson(bson)
            JobPlanner.add_date(bson)
            try:
                doc_id = db['jobs'].insert_one(bson).inserted_id
                Pasi.log(f"Inserted job {doc_id} into db", "info")
            except pymongo.errors.DuplicateKeyError:
                errmsg = f"Unable to create job, job already exists"
                Pasi.log(errmsg, 'warning')
                sg.PopupError(errmsg, keep_on_top=True)


class JobPlannerCheckdb(JobPlanner):
    @staticmethod
    def run(win, event, values):
        if JobPlanner.form_ok(values, ignore=["!name"]):
            # display raw bson document in pop up box query from name
            bson = db['jobs'].find_one({'name': values['name']})

            bson = pp.pformat(
                bson) if bson is not None else "Job does not exist."
            sg.PopupOK(bson,
                       title=f"Job `{values['name']}``",
                       keep_on_top=True)


class JobPlannerUpdatedb(JobPlanner):
    @staticmethod
    def run(win, event, values):
        if JobPlanner.form_ok(values, ignore=["main_menu", "passes"]):
            bson = values.copy()
            JobPlanner.remove_from_values(bson, to_remove=["main_menu"])
            JobPlanner.clean_bson(bson)
            JobPlanner.add_date(bson)

            filt = {"name": values['name']}
            print(bson)
            result = db['jobs'].update_one(filter=filt,
                                           update={
                                               "$set": bson
                                           },
                                           upsert=False).matched_count
            print(result)
            if result < 1:
                sg.PopupError(f"{values['name']} does not exist, save first.",
                              keep_on_top=True)
            else:
                sg.PopupOK(f"{values['name']} successfully updated",
                           keep_on_top=True)


class JobPlannerNewJob(JobPlanner):
    @staticmethod
    def run(win, event, values):
        widget_names = values.copy()
        JobPlanner.remove_from_values(widget_names, to_remove=["main_menu"])
        JobPlanner.add_date(widget_names)
        for name, val in widget_names.items():
            if isinstance(val, list):
                win[name]([])

            if isinstance(val, str):
                win[name]("")

        # dont forget date
        win['date'](str(widget_names['date']))


class JobPlannerLoadJob(JobPlanner):
    @staticmethod
    def run(win, event, values):
        all_jobs = db['jobs'].find()

        jobs = {}
        for job in all_jobs:
            jobs[job['name']] = job

        layout = [[
            sg.Listbox(list(jobs.keys()),
                       size=(MainWindowLayout.width // 4,
                             MainWindowLayout.height // 4),
                       key="job_selection",
                       enable_events=True,
                       select_mode=sg.SELECT_MODE_SINGLE)
        ]]

        win2 = sg.Window("Select Job",
                         keep_on_top=True,
                         layout=layout,
                         size=(MainWindowLayout.width // 2,
                               MainWindowLayout.height // 2),
                         finalize=True)

        job_name = None
        while True:
            ev2, val2 = win2.read()

            if ev2 == None:
                break

            if ev2 == "job_selection":
                job_name = val2[ev2][0]
                win2.close()
                break

        if job_name is None:
            # do nothing
            return

        job = jobs[job_name]  # bson/dict object
        for name, _ in values.items():
            if name in job.keys():
                win[name].update(job[name])

        # done forget about the date :)
        win['date'](job['date'])
