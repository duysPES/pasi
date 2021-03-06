import os, sys
import tkinter as tk
import PySimpleGUI as sg
from multiprocessing import Process, Queue
import datetime
import time

from pysrc import db, config
from pysrc.db import Log
import pysrc.log as log
from pysrc import config
from pysrc.switch import Switch
from pysrc.lisc import LISC
from pysrc.commands import Status
from pysrc.layout import ShootingLayout, MainWindowLayout, JobPlannerLayout, ViewLogLayout, ChangeExpectedAmountLayout, ShootingPanelMenuBar
from pysrc.colors import set_dark, FIRING_BUTTONS
from pysrc.thread import queuer, threader, InfoType, ConnMode
from pysrc.jobplanner import JobPlannerCheckdb, JobPlannerLoadJob, JobPlannerNewJob, JobPlannerSave, JobPlannerUpdatedb, JobPlannerShowPass, JobPlanner
from pysrc.job import Job, Pass

if config.pasi("theme") == "dark":
    set_dark()
else:
    sg.change_look_and_feel("Reddit")


class ShootingPanel:
    """
    Base functions that maniuplate GUI within 
    the shooting panel section of the app.

    All sub-classes uses the same function `SubClass.run(win, events, values)`
    """
    @staticmethod
    def set_window_title(win, msg):
        msg = f"PASI v{config.pasi('version')} {msg}"
        win.TKroot.title(msg)

    @staticmethod
    def debug_log(win, msg, status):
        Pasi.log(msg, status)
        Inventory.debug_area(win, msg=msg, clear=False)

    @staticmethod
    def __edit_ml(widget, msg, clear=False):
        if clear:
            widget("")
        else:
            current = widget.get()
            widget(current + str(msg))

    @staticmethod
    def debug_area(win, msg, clear=False):
        Inventory.__edit_ml(win['debug_area'], msg=msg, clear=clear)

    @staticmethod
    def update_switch_canvas(win, switch=None, clear=False):
        switch_lst = win['switch_list']

        if clear:
            switch_lst.clear()
            return

        if not isinstance(switch, Switch):
            raise ValueError(f"{switch} is not of type Switch")

        switches = switch_lst.GetListValues()

        if len(switches) == 0:
            switches.append(str(switch))
            switch_lst.Update(switches)
            return

        found = list(filter(lambda sw: sw == str(sw), switches))

        if len(found) > 0:
            Pasi.log(f"Switch already accounted for: {switch}", 'info')
        else:
            switches.append(str(switch))
            switch_lst.Update(switches)
        return


class ChangeExpectedAmount(ShootingPanel):
    """
    Changes the Expected Amount for switches
    """
    @staticmethod
    def run(win, event, values):
        win.Hide()
        layout = ChangeExpectedAmountLayout()
        win2 = sg.Window("Edit Expected Amount",
                         layout=layout.main_layout(),
                         size=(layout.width, layout.height),
                         finalize=True,
                         keep_on_top=True)

        while True:
            ev2, val2 = win2.read()

            if val2 is None:
                break

            if ev2 == "Exit":
                cur_val = val2['expected_combo']

                config.update_switches("expected",
                                       str(val2['expected_combo']),
                                       dump=True)

                win['label_expected_amount'](str(val2['expected_combo']))
                break
        win2.close()
        win.UnHide()


class Inventory(ShootingPanel):
    """
    Executes the Inventory procedure. Inventorying switches on the line
    """
    @staticmethod
    def send_mode(win, mode, payload):
        if mode == ConnMode.DEBUG:
            Inventory.debug_area(win, msg=payload, clear=False)

        elif mode == ConnMode.MAIN:
            print("FROM MAIN ", payload)

        elif mode == ConnMode.STATUS:
            status = Status(payload)
            msg = f"{status.voltage}V, {status.temp}C <FW {status.firmware}>"
            print(msg)
            Inventory.set_window_title(win, msg=msg)

    @staticmethod
    def process_message(win, msgs):
        """
        process incoming message from inventory queue
        """
        if not isinstance(msgs, deque):
            errmsg = "Message from queue is not a ConnPackage, fatal error."
            Inventory.debug_log(win, msg=errmsg, status='error')
            return False

        elif len(msgs) > 0:

            with Log(db.activate_pass()) as l:
                info_type, mode, msg = msgs
                if info_type == InfoType.KILL:
                    msgs = "Done with inventory process"
                    Inventory.send_mode(win, mode, msg)
                    Pasi.log(msg, 'info')
                    l.log(msg, 'info')
                    return False
                #TODO: correctly log output from LISC
                if info_type == InfoType.SWITCH:
                    if mode == ConnMode.STATUS:
                        pos, addr, status = msg
                        Inventory.send_mode(win, mode, status)
                        l.log(f"Found switch {pos}: {addr}", status)
                        return True

                    elif mode == ConnMode.MAIN:
                        pos, addr = msg
                        # update anticipated HERE
                        sg = f"add switch: {pos}: [{addr}]"
                        return True

                elif info_type == InfoType.OTHER:
                    Inventory.send_mode(win, mode, msg)
                    return True
                else:
                    pass

    @staticmethod
    def run(win, event, values):

        log.Log.clear(log.LogType.gui)
        Inventory.debug_area(win, None, clear=True)
        Pasi.log("Beginning inventory run", "info")
        expected_switches = int(win['label_expected_amount'].DisplayText)

        Inventory.debug_log(win, f"Expecting {expected_switches} switches.",
                            'info')

        port = config.lisc('port')
        baudrate = config.lisc("baudrate")
        with LISC(port=port, baudrate=baudrate, timeout=3) as lisc:
            # queuer.add('inventory', Queue())

            Pasi.log("Spawning thread for inventory run", 'info')
            thread = Process(target=lisc.do_inventory,
                             args=(expected_switches, ))
            # threader.add('inventory', thread)
            # queuer.send('inventory', 'start')
            # threader.start('inventory')
            thread.start()


class ViewLogs(ShootingPanel):
    """
    brings up Logs associated with the currently selected
    Pass that is connected to a specific job.
    """
    @staticmethod
    def run(win, event, values):
        win.Hide()
        layout = ViewLogLayout()
        win2 = sg.Window("Logs",
                         layout=layout.main_layout(),
                         size=(layout.width, layout.height),
                         finalize=True,
                         keep_on_top=True)
        prev_file_buf = ""

        try:
            active_pass = db.attached_job().get_active_pass()
            while True:
                ev2, val2 = win2.read(timeout=3)

                # TODO: Find a better way to retrieve log contents of pass,
                # current implementation creates a new class instance
                # every call
                buffer = Log.get_contents(active_pass)

                if prev_file_buf != buffer:
                    win2['log_view'](buffer)
                    prev_file_buf = buffer

                # with open((log.LOG_PATH / "gui.log").resolve(), "r") as l:
                #     buffer = l.read()
                #     if prev_file_buf != buffer:
                #         win2['log_view'](buffer)
                #         prev_file_buf = buffer

                if ev2 is None or ev2 == "Exit":
                    win2.close()
                    break
        except IndexError:
            # there are no passes for this job.
            sg.PopupError("There are no passes attached to this job.",
                          keep_on_top=True)

        win2.close()
        win.UnHide()


class DetachJob(ShootingPanel):
    """
    Detaches the Job for shooting panel.
    Sets attached_job in db to null, and changes
    elements to make certain things uneditable.
    """
    @staticmethod
    def run(parent, win, event, values):
        win['button_inventory'].Update(disabled=True)
        win['main_menu'].set_element("Attach Job", 1)
        win['main_menu'].set_element("Detach Job", 0)
        win['main_menu'].set_element("View Logs", 0)
        win['main_menu'].set_element("Passes", 0)
        win['main_menu'].reset()

        attached_job = db.attached_job()
        if attached_job is not None:
            db.update_jobs(filter={"_id": attached_job._id},
                           update_query={"$set": {
                               "active_pass": None
                           }})
        db.detach_job()


class AttachJob(ShootingPanel):
    """
    Displays the list of all jobs in database and attaches 
    selected job in database.
    """
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
            return

        if not db.attach_job(job_name):
            errmsg = "Fatal error, could not attach job, doesn't exist in db"
            Pasi.log("Fatal error, could not attach job, doesn't exist in db"
                     "error")
            sg.PopupError(
                "Fatal error, could not attach job, doesn't exist in db",
                keep_on_top=True)
            return


class Pasi:
    """
    Main app class, handles Job Planner and Shooting Interface GUIs.
    """
    inventory = False

    def win_title(self, msg=""):
        """
        Change the window title 
        """
        return f"PASI v{config.pasi('version')} {msg}"

    def create_new_pass(self, win):
        win['button_inventory'].Update(disabled=False)

        # create a pass object and all output from shooting
        # panel will be stored in currently selected pass
        self.attached_job = db.attached_job()

        print("Job: ", self.attached_job)
        new_pass: Pass = Pass(
            len(self.attached_job.pass_objs()) + 1, self.attached_job.id)

        menu: ShootingPanelMenuBar = win['main_menu']

        # add active pass

        # add to menubar
        menu.add_passes([new_pass], append=True)

        # add to database and make new pass active
        db.add_pass(new_pass, make_active=True)

        # add an example log to pass
        with Log(new_pass) as l:
            l.log(
                f"Pass{new_pass.num} created for <Job {self.attached_job.id}>",
                "info")
        win.TKroot.title(
            self.win_title(msg=self.attached_job.for_win_title(new_pass)))

    def __init__(self):
        self.shooting_interface_layout = ShootingLayout()
        self.main_layout = MainWindowLayout()
        self.job_plan_layout = JobPlannerLayout()
        self.height = self.main_layout.height
        self.width = self.main_layout.width
        self.window = sg.Window(self.win_title(),
                                layout=self.main_layout.main_layout(),
                                grab_anywhere=False,
                                size=(self.main_layout.width,
                                      self.main_layout.height),
                                finalize=True,
                                resizable=False,
                                keep_on_top=True)
        self.attached_job = None

    def loop(self):
        """
        main loop of the app, everything happens here.
        """
        shooting_win_active = False
        job_win_active = False
        async_ = config.pasi('async_timeout')
        while True:
            event, values = self.window.read(timeout=async_)

            if event != '__TIMEOUT__':
                pass
            if event in (None, "Quit"):
                threader.join()
                break

            if 'Job Planner' == event and not job_win_active:
                job_win_active = True
                self.window.Hide()
                layout = self.job_plan_layout.main_layout()
                win = sg.Window(f"{self.win_title(': Job Planner')}",
                                layout=layout,
                                size=(self.width, self.height),
                                keep_on_top=True)

                while True:
                    ev2, val2 = win.read()

                    if not self.handle_job_planner(win, ev2, val2):
                        win.close()
                        job_win_active = False
                        self.window.UnHide()
                        break

            if 'Shooting Interface' == event and not shooting_win_active:
                shooting_win_active = True
                self.window.Hide()
                layout = self.shooting_interface_layout.main_layout()
                win = sg.Window(f"{self.win_title(': Shooting Interface')}",
                                layout=layout,
                                size=(self.width, self.height),
                                keep_on_top=True,
                                finalize=True)
                DetachJob.run(self, win, event, values)
                win.TKroot.title(self.win_title(f": Shooting Interface"))
                self.attached_job = None

                while True:
                    ev2, val2 = win.read(timeout=200)

                    if not self.handle_shooting_interface(win, ev2, val2):
                        win.close()
                        shooting_win_active = False
                        self.window.UnHide()
                        break

            if 'Dark' == event:
                # change theme in config, restart program
                config.update_theme("dark")
                self.__restart()

            if 'Light' == event:
                # change theme in config, restart program
                config.update_theme("light")
                self.__restart()

        config.write_ini()

    def handle_shooting_interface(self, win, event, values):
        """
        Spawns the GUI for Shooting Interface and handles all reactions here.
        """
        if event is None or event == "Exit":
            return False

        if not self.attached_job:
            if db.attached_job() is not None:
                # win['button_inventory'].Update(disabled=False)
                menu: ShootingPanelMenuBar = win['main_menu']
                menu.set_element("Attach Job", 0)
                menu.set_element("Detach Job", 1)
                menu.set_element("View Logs", 1)
                menu.set_element("Passes", 1)
                job: Job = db.attached_job()
                self.attached_job = job

                pass_objs = job.pass_objs()

                if len(pass_objs) > 0:
                    menu.add_passes(pass_objs)
                    db.activate_pass(pass_objs[-1])

                    win_msg = job.for_win_title(pass_objs[-1])
                else:
                    # have win_msg just show name and client:
                    win_msg = f"< {job.name}:{job.client} >"

                win.TKroot.title(self.win_title(msg=win_msg))

        else:
            if event == "New::new_pass":
                self.create_new_pass(win)
                # # create a pass object and all output from shooting
                # # panel will be stored in currently selected pass
                # self.attached_job = db.attached_job()

                # print("Job: ", self.attached_job)
                # new_pass: Pass = Pass(
                #     len(self.attached_job.pass_objs()) + 1,
                #     self.attached_job.id)

                # menu: ShootingPanelMenuBar = win['main_menu']

                # # add active pass

                # # add to menubar
                # menu.add_passes([new_pass], append=True)

                # # add to database and make new pass active
                # db.add_pass(new_pass, make_active=True)

                # # add an example log to pass
                # with Log(new_pass) as l:
                #     l.log(
                #         f"Pass{new_pass.num} created for <Job {self.attached_job.id}>",
                #         "info")
                # win.TKroot.title(
                #     self.win_title(
                #         msg=self.attached_job.for_win_title(new_pass)))

        # we do not want user to directly change pass contents
        # so if selected pass is click, disable inventory
        if self.attached_job is not None:
            if event in [str(p) for p in self.attached_job.pass_objs()]:
                # print("FOUND A PASS, ", event)
                win['button_inventory'].Update(disabled=True)
                sg.PopupQuickMessage("*** Readonly ***", keep_on_top=True)

                job: Job = self.attached_job
                pass_name: str = event
                # find pass
                p = job.get_pass_by_name(pass_name)
                db.activate_pass(p)
                self.attached_job = db.attached_job()
                win.TKroot.title(
                    self.win_title(msg=self.attached_job.for_win_title(p)))

        if self.inventory == False:
            try:
                start_msg = queuer.recv_nowait('inventory')
                if start_msg == "start":
                    self.inventory = True
            except:
                pass
        else:
            try:
                msgs = queuer.recv_nowait('inventory')

                self.inventory = Inventory.process_message(win, msgs)
            except:

                pass

        if "View Logs" == values["main_menu"]:
            ViewLogs.run(win, event, values)

        if "Changed Expected Amount" in event:
            ChangeExpectedAmount.run(win, event, values)

        if 'Attach Job' == event:
            AttachJob.run(win, event, values)

        if 'Detach Job' == event:
            DetachJob.run(self, win, event, values)
            win.TKroot.title(self.win_title(f": Shooting Interface"))
            self.attached_job = None

        if event == "button_inventory":
            Inventory.run(win, event, values)
            # global cntr
            # btns = [
            #     win['button_prearm'], win['button_arm'], win['button_fire']
            # ]

            # active_theme = config.get_theme()
            # btns[cntr].Update(
            #     button_color=FIRING_BUTTONS[active_theme]['active'],
            #     disabled=False)
            # cntr += 1
            # print(btns)
            # test change

        # if event != "__TIMEOUT__":
        #     # print(event)
        #     # print("")

        return True

    def handle_job_planner(self, win, event, values):
        """
        spawns the GUI for job planning and handles all reactions here.
        """
        if event is None or event == "Exit":
            return False

        JobPlanner.format(values)

        if event == "today_button":
            date_widget = win['date']
            date = str(datetime.datetime.now())
            date_widget(str(date))

        if event == "Save":
            JobPlannerSave.run(win, event, values)

        if event == "check_db_btn":
            JobPlannerCheckdb.run(win, event, values)

        if event == "update_db_btn":
            JobPlannerUpdatedb.run(win, event, values)

        if event == "Load":
            JobPlannerLoadJob.run(win, event, values)

        if event == "New":
            JobPlannerNewJob.run(win, event, values)

        if event == "passes":
            JobPlannerShowPass.run(win, event, values)

        # if event != "__TIMEOUT__":
        # print(event, values)
        # pass

        # update time

        return True

    def __restart(self):
        """
        Helper code to restart the app.
        First writes the current config settings in database to flat file.
        """
        config.write_ini()
        python = sys.executable
        os.execl(python, python, *sys.argv)

    @staticmethod
    def log(msg, status='info'):
        """
        ```python
        input: str
        return: None
        ```
        Wrapper around log object to verify that output from GUI is going to gui.log
        """
        log.log(status)(msg, log.LogType.gui)
