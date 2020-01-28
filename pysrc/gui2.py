from pysrc import config
import pysrc.log as log
from pysrc.log import LogType
from pysrc.log import LOG_PATH
import PySimpleGUI as sg
from pysrc.layout import ShootingLayout, MainWindowLayout, JobPlannerLayout
from multiprocessing import Process, Queue

sg.change_look_and_feel('Reddit')


class Pasi:
    @property
    def win_title(self):
        return f"PASI v{config.pasi('version')}"

    def __init__(self):
        self.shooting_interface_layout = ShootingLayout()
        self.main_layout = MainWindowLayout()
        self.job_plan_layout = JobPlannerLayout()
        self.inventory_queue = Queue()
        self.height = self.main_layout.height
        self.width = self.main_layout.width
        print("HELLO")
        self.window = sg.Window(self.win_title,
                                layout=self.main_layout.main_layout(),
                                grab_anywhere=False,
                                size=(self.main_layout.width,
                                      self.main_layout.height),
                                finalize=True,
                                resizable=False,
                                keep_on_top=True)

    def loop(self):
        shooting_win_active = False
        job_win_active = False
        while True:
            event, values = self.window.read(
                timeout=config.pasi("async_timeout"))

            if event != '__TIMEOUT__':
                pass
            if event in (None, "Quit"):
                break

            if 'Job Planner' == event and not job_win_active:
                job_win_active = True
                self.window.Hide()
                layout = self.job_plan_layout.main_layout()
                win = sg.Window(f"{self.win_title}: Job Planner",
                                layout=layout,
                                size=(self.width, self.height),
                                keep_on_top=True)

                while True:
                    ev2, val2 = win.read()

                    if not self.handle_job_planner(ev2, val2):
                        win.close()
                        job_win_active = False
                        self.window.UnHide()
                        break

            if 'Shooting Interface' == event and not shooting_win_active:
                shooting_win_active = True
                self.window.Hide()
                layout = self.shooting_interface_layout.main_layout()
                win = sg.Window(f"{self.win_title}: Shooting Interface",
                                layout=layout,
                                size=(self.width, self.height),
                                keep_on_top=True)

                while True:
                    ev2, val2 = win.read()

                    if not self.handle_shooting_interface(ev2, val2):
                        win.close()
                        shooting_win_active = False
                        self.window.UnHide()
                        break

    def handle_shooting_interface(self, event, values):
        if event is None or event == "Exit":
            return False
        return True

    def handle_job_planner(self, event, values):
        if event is None or event == "Exit":
            return False
        return True

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
