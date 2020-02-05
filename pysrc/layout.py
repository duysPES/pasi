import PySimpleGUI as sg
from pysrc import config, db
import sys, os
from pysrc.log import LOG_PATH
from pathlib import Path
import datetime
from pysrc.job import Pass, Job
from typing import *
resources = Path(__file__).parent.parent / "resources/"


# MAIN_MENU = []


class ShootingPanelMenuBar(sg.Menu):
    MENU = [
    ["&File", ["&Attach Job", "!&Detach Job", "&View Logs", "&Changed Expected Amount"]],
    ["!&Passes", ["&New::new_pass"]]
    ]

    def set_element(self, name: str, state=1, visible=None):
        prepend = "!" if state == 0 else ""
        new_menu = self.MENU[:]

        for i, _ in enumerate(new_menu):
            for idx, element in enumerate(new_menu[i]):
                if isinstance(element, list):
                    for idy, sub_element in enumerate(new_menu[i][idx]):
                        parsed = sub_element.replace('!', '')
                        if parsed.replace("&", "") == name:
                            new_menu[i][idx][idy] = prepend + parsed

                if isinstance(element, str):
                    parsed = element.replace('!', '')
                    if parsed.replace("&", "") == name:
                        new_menu[i][idx] = prepend + parsed

        self.Update(menu_definition=new_menu, visible=visible)

    def reset(self):
        self.Update(menu_definition=ShootingPanelMenuBar.MENU)

    def add_passes(self, names: List[Pass] ,append=False):
        """
        add passes to menu, under passes
        """

        # make a copy of self.MENU
        new_menu = self.MENU[:]

        # strip all options in menu under pass except for
        # menu option "new"
        stripped_vals = new_menu[1][1][:1]
        old_vals = new_menu[1][1][1:]
        if append:
            [stripped_vals.append(x) for x in old_vals]
        # for pass name in provided list of passes
        for p in names:
            stripped_vals.append(str(p))

        new_menu[1][1] = stripped_vals
        self.Update(menu_definition=new_menu)



class Layout:

    width = int(config.pasi("width"))
    height = int(config.pasi("height"))

class MainWindowLayout(Layout):
    def menu_bar(self):
        layout = sg.Menu([[
            "&File",
            [
                "&Job Planner", "&Shooting Interface", "&Change Theme",
                ['&Dark', '&Light']
            ]
        ]],
                         tearoff=False,
                         key="main_menu")
        return layout

    def main_layout(self):
        logo_path = (resources / "logo.png").resolve()
        layout = [[self.menu_bar(), sg.Text('', size=(0, 5))],
                  [
                      sg.Column(
                          layout=[
                              [sg.Image(logo_path, pad=(0, 10))],
                          ],
                          justification="center",
                      )
                  ]]

        return layout


class JobPlannerLayout(Layout):
    def menu_bar(self):
        layout = sg.Menu([["&Jobs", ["&New", "&Load"]]], tearoff=False, key="main_menu")
        return layout

    def column1_layout(self):
        layout = sg.Column(justification='left',
                           layout=[[
                               sg.Frame('',
                                        border_width=0,
                                        layout=[
                                            [
                                                sg.Text("Job Name",
                                                        size=(8, 1)),
                                                sg.Input("",
                                                         size=(17, 1),
                                                         key="name")
                                            ],
                                            [
                                                sg.Text("Client", size=(8, 1)),
                                                sg.Input("",
                                                         size=(17, 1),
                                                         key="client")
                                            ],
                                            [
                                                sg.Text("Well", size=(8, 1)),
                                                sg.Input("",
                                                         size=(17, 1),
                                                         key="well")
                                            ],
                                            [
                                                sg.Text("Unit #", size=(8, 1)),
                                                sg.Input("",
                                                         size=(17, 1),
                                                         key="unit")
                                            ],
                                        ])
                           ]])



        return layout

    def column2_layout(self):
        layout = sg.Column(justification='center',
            layout=[
                [sg.Frame('Date',
                    layout=[
                        # [sg.Button("Update", key='today_button', font=("fixedsys", "6"))],
                        [sg.Text(f"{str(datetime.datetime.now())}", key='date', font=("fixedsys", "6"))]
                    ])
                ],
            ]
        )
        return layout

    def main_layout(self):
        layout = [
            [self.menu_bar()],
            [self.column1_layout(), self.column2_layout()],
            [sg.Frame('Notes',
                    border_width=1,
                    layout=[[sg.Multiline("", key="notes", size=(self.width // 15, self.height//200), font=("fixedsys", "7"))]])
            ],
            [sg.Save(), sg.Button("Update", key="update_db_btn"), sg.Button("check db", key='check_db_btn')],
            [
                sg.Frame('Passes', pad=(0,50),
                        layout=[
                            [sg.Listbox([], key="passes", enable_events=True, disabled=False, auto_size_text=True, size=(self.width // 15, self.height // 200))]
                        ])
            ]
        ]

        return layout


class ShootingLayout(Layout):
    checkmark = u'\u2713'

    def main_menu(self):

        # layout = Menu(MAIN_MENU).widget(tearoff=False, key="main_menu")
        layout = ShootingPanelMenuBar(ShootingPanelMenuBar.MENU,
                                      tearoff=False,
                                      key="main_menu")
        return layout

    def anticipated_layout(self):
        layout = [[sg.Text('Anticipated', key='label_anticipated')],
                  [
                      sg.Frame('',
                               border_width=1,
                               layout=[
                                   [
                                       sg.Text('0',
                                               size=(2, 1),
                                               font='any 16',
                                               key='label_anticipated_amount')
                                   ],
                               ])
                  ]]
        return layout

    def expected_layout(self):
        expected = config.switches("expected")
        layout = [[sg.Text('Expected', key='label_expected')],
                  [
                      sg.Frame('',
                               border_width=1,
                               layout=[
                                   [
                                       sg.Text(str(expected),
                                               size=(2, 1),
                                               font='fixedsys 16',
                                               key='label_expected_amount'
                                               )
                                   ],
                               ])
                  ]]
        return layout

    def column1_layout(self):
        layout = sg.Column(layout=[
            [
                sg.Button("Inventory",
                          bind_return_key=True,
                          size=(20, 3),
                          key="button_inventory",
                          border_width=5,
                          disabled=True)
            ],
            [sg.Frame('', border_width=0, layout=[[]], pad=(0, 100))],
            [
                sg.Button("Pre-Arm",
                          key="button_prearm",
                          size=(20, 3),
                          disabled=True,
                          border_width=5)
            ],
            [
                sg.Button("Arm",
                          key="button_arm",
                          disabled=True,
                          size=(20, 3),
                          border_width=5)
            ],
            [
                sg.Button(
                    "Fire",
                    disabled=True,
                    key="button_fire",
                    size=(20, 3),
                    border_width=5)
            ]
        ])

        return layout

    def column2_layout(self):

        layout = sg.Column(layout=[
            [
                sg.Frame('', border_width=0, layout=self.anticipated_layout()),
                sg.Frame('', border_width=0, layout=self.expected_layout())

            ],
            [
                sg.Listbox(values=[],
                           size=(self.width*2, self.height//50),
                           key='switch_list',
                           enable_events=True,
                           font=("fixedsys", '7'))
            ]
        ])
        return layout

    def debug_area(self):
        layout = sg.Multiline(default_text='',
                              size=(self.width*2, self.height//100),
                              key="debug_area",
                              do_not_clear=True,
                              disabled=True)
        return layout

    def main_layout(self):
        layout = [[
            self.main_menu(),
            self.column1_layout(),
            self.column2_layout()
        ], [self.debug_area()]]
        return layout


class ViewLogLayout(Layout):
    def main_layout(self):
        layout = [[
            sg.Multiline("",
                         size=(self.width, self.height),
                         key="log_view",
                         disabled=True,
                         font=("fixedsys", "5"))
        ]]
        return layout


class ChangeExpectedAmountLayout(Layout):
    def main_layout(self):
        layout = [[sg.Text("Choose Expected Number of Switches")],
                  [
                      sg.Combo([x + 1 for x in range(50)],
                               key='expected_combo',
                               size=(50, 1),
                               default_value=config.switches("expected"))
                  ], [sg.Exit(bind_return_key=True)]]
        return layout
