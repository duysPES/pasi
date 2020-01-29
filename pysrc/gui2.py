from pysrc import config
import pysrc.log as log
from pysrc.log import LogType, LOG_PATH
from pysrc.switch import Switch
from pysrc.lisc import LISC
import PySimpleGUI as sg
from pysrc.commands import Status
from pysrc.layout import ShootingLayout, MainWindowLayout, JobPlannerLayout, ViewLogLayout, ChangeExpectedAmountLayout
from multiprocessing import Process, Queue
from pysrc.colors import set_dark, FIRING_BUTTONS
from pysrc.thread import queuer, threader, InfoType, ConnMode
import os, sys
from collections import deque

set_dark()

if config.pasi("theme") == "dark":
    set_dark()
else:
    sg.change_look_and_feel("Reddit")

cntr = 0


class ChangeExpectedAmount:
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

            if ev2 in (None, "Exit"):
                config.update_switches("expected",
                                       str(val2['expected_combo']),
                                       dump=True)
                win['label_expected_amount'](str(val2['expected_combo']))
                win2.close()
                break

        win.UnHide()


class Inventory:
    @staticmethod
    def set_window_title(win, msg):
        msg = f"PASI v{config.pasi('version')} {msg}"
        win.TKroot.title(msg)

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
        print(msgs)
        if not isinstance(msgs, deque):
            errmsg = "Message from queue is not a ConnPackage, fatal error."
            Inventory.debug_log(win, msg=errmsg, status='error')
            return False

        elif len(msgs) > 0:
            info_type, mode, msg = msgs
            if info_type == InfoType.KILL:
                msgs = "Done with inventory process"
                Inventory.send_mode(win, mode, msg)
                Pasi.log(msg, 'info')
                return False

            if info_type == InfoType.SWITCH:
                if mode == ConnMode.STATUS:
                    pos, addr, status = msg
                    Inventory.send_mode(win, mode, status)
                    return True

                elif mode == ConnMode.MAIN:
                    pos, addr = msg
                    # update anticipated HERE
                    # @TODO
                    sg = f"add switch: {pos}: [{addr}]"
                    print(sg)
                    return True

            elif info_type == InfoType.OTHER:
                Inventory.send_mode(win, mode, msg)
                return True
        else:
            pass

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

    @staticmethod
    def run(win, event, values):

        log.Log.clear(LogType.gui)
        Inventory.debug_area(win, None, clear=True)
        Pasi.log("Beginning inventory run", "info")
        expected_switches = int(win['label_expected_amount'].DisplayText)

        Inventory.debug_log(win, f"Expecting {expected_switches} switches.",
                            'info')

        port = config.lisc('port')
        baudrate = int(config.lisc("baudrate"))

        # with LISC(port=port, baudrate=baudrate, timeout=3) as lisc:
        #     queuer.add('inventory', Queue())

        #     Pasi.log("Spawning thread for inventory run", 'info')
        #     thread = Process(target=lisc.do_inventory,
        #                      args=(expected_switches, ))
        #     threader.add('inventory', thread)
        #     queuer.send('inventory', 'start')
        #     thread.start()

    @staticmethod
    def debug_log(win, msg, status):
        Pasi.log(msg, status)
        Inventory.debug_area(win, msg=msg, clear=False)


class ViewLogs:
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
        while True:
            ev2, val2 = win2.read(timeout=3)

            with open(LOG_PATH + "gui.log", "r") as l:
                buffer = l.read()
                if prev_file_buf != buffer:
                    win2['log_view'](buffer)
                    prev_file_buf = buffer
            if ev2 is None or ev2 == "Exit":
                win2.close()
                break
        win.UnHide()


class Pasi:
    inventory = False

    @property
    def win_title(self):
        return f"PASI v{config.pasi('version')}"

    def __init__(self):
        self.shooting_interface_layout = ShootingLayout()
        self.main_layout = MainWindowLayout()
        self.job_plan_layout = JobPlannerLayout()
        self.height = self.main_layout.height
        self.width = self.main_layout.width
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
                threader.join()
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

                    if not self.handle_job_planner(win, ev2, val2):
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
                    ev2, val2 = win.read(timeout=1)

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

    def handle_shooting_interface(self, win, event, values):
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

        if event is None or event == "Exit":
            return False

        if "View Logs" == values["main_menu"]:
            ViewLogs.run(win, event, values)

        if "Changed Expected Amount" in event:
            ChangeExpectedAmount.run(win, event, values)

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

        if event != "__TIMEOUT__":
            print(event)

        return True

    def handle_job_planner(self, win, event, values):
        if event is None or event == "Exit":
            return False
        return True

    def __restart(self):
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
