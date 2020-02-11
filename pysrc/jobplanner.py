import pymongo
import PySimpleGUI as sg
import datetime
from pysrc import db, config
from pysrc.job import Pass, Job
from pysrc.layout import MainWindowLayout
from pysrc.db import Bson, Log
from typing import *


class JobPlanner:
    @staticmethod
    def check_element(values, key, invalid=''):
        if values[key].strip() == invalid:
            return False
        return True

    @staticmethod
    def format(values):
        to_skip = ['passes', 'notes']

        for key, val in values.items():
            if key not in to_skip:
                try:
                    values[key] = val.upper()
                except AttributeError:
                    # most likely a None, leave it alone
                    pass

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


class JobPlannerSave(JobPlanner):
    @staticmethod
    def run(win, event, values):
        # first check to see if any of the fields are empty
        if JobPlanner.form_ok(values, ignore=["main_menu", "passes"]):
            # form is okay, construct bson document
            bson = Bson(values.copy()).clean_bson().add_date().add_field(
                "active_pass", None)

            JobPlanner.remove_from_values(bson, to_remove=["main_menu"])
            try:
                # doc_id = db['jobs'].insert_one(bson).inserted_id
                doc_id = db.add_job(bson)
                db.log(f"Inserted job {doc_id} into db", "info")
            except pymongo.errors.DuplicateKeyError:
                errmsg = f"Unable to create job, job already exists"
                db.log(errmsg, 'warning')
                sg.PopupError(errmsg, keep_on_top=True)


class JobPlannerCheckdb(JobPlanner):
    @staticmethod
    def run(win, event, values):
        if JobPlanner.form_ok(values, ignore=["!name"]):
            # display raw bson document in pop up box query from name
            # bson = db['jobs'].find_one({'name': values['name']})
            job = db.find_job(job_name=values['name'])

            job = str(job) if job is not None else "Job does not exist."
            sg.PopupOK(job, title=f"Job `{values['name']}``", keep_on_top=True)


class JobPlannerUpdatedb(JobPlanner):
    @staticmethod
    def run(win, event, values):
        if JobPlanner.form_ok(values, ignore=["main_menu", "passes"]):
            bson = Bson(values.copy())
            JobPlanner.remove_from_values(bson,
                                          to_remove=["main_menu", "passes"])
            bson.clean_bson().add_date()
            filt = {"name": values['name']}
            result = db.update_jobs(filter=filt, update_query={"$set": bson})

            if result < 1:
                sg.PopupError(f"{values['name']} does not exist, save first.",
                              keep_on_top=True)
            else:
                sg.PopupOK(f"{values['name']} successfully updated",
                           keep_on_top=True)


class JobPlannerNewJob(JobPlanner):
    @staticmethod
    def run(win, event, values):
        widget_names = Bson(values.copy()).add_date()
        JobPlanner.remove_from_values(widget_names, to_remove=["main_menu"])
        for name, val in widget_names.items():
            if isinstance(val, list):
                win[name]([])

            if isinstance(val, str):
                win[name]("")

        # dont forget date
        win['date'](str(widget_names['date']))


class JobPlannerShowPass(JobPlanner):
    @staticmethod
    def run(win, event, values):

        # a little hack and pretty confusing for the future
        # This method is only run when an event IS 'passes'
        # which tells us that the user is looking for more information on
        # a specific pass, it will have the name of the pass as the
        # value of the dictionary that holds the forms key:value pairs,
        # in this case, we are guarenteed that values (the dict) contains
        # the key of event (the key='passes'); and therefore
        # values[event] == {name of pass}
        selected_pass = values[event]
        job = db.find_job(values['name'])

        # because we are querying a potential list of items from
        # a ListBox, the value of values[event] is a list,
        # since we put the restriction on that the user can ONLY
        # select a single value on the Pass ListBox, we are guaranteed
        # that the list will only ever have a single element,
        # but checking for more than one should still be done.)

        if len(selected_pass) > 1:
            raise IndexError("Selected pass contains more than one element.")

        p = job.get_pass_by_name(*selected_pass)

        log = Log.get_contents(p)

        p.add_log(log)

        sg.PopupOK(p.summary(), title=f"{p}", keep_on_top=True)


class JobPlannerLoadJob(JobPlanner):
    @staticmethod
    def run(win, event, values):
        jobs = db.all_jobs()

        layout = [[
            sg.Listbox(list(jobs.keys()),
                       size=(MainWindowLayout().width // 4,
                             MainWindowLayout().height // 4),
                       key="job_selection",
                       enable_events=True,
                       select_mode=sg.SELECT_MODE_SINGLE)
        ]]

        win2 = sg.Window("Select Job",
                         keep_on_top=True,
                         layout=layout,
                         size=(MainWindowLayout().width // 2,
                               MainWindowLayout().height // 2),
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
                # print("key ", name, " val: ", job.d[name], " updating: ",
                #       win[name])
                if isinstance(job.d[name], list):
                    passes = [j['name'] for j in job.d[name]]

                    win[name].Update(passes)
                else:
                    win[name].Update(job.d[name])

        # done forget about the date :)
        win['date'](job.date)
