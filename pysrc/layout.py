import PySimpleGUI as sg
from pysrc import config
import sys, os
resources = os.path.join(os.getenv("HOME"), "pasi/resources/")

class MainWindowLayout:
    width = config.pasi('width')
    height = config.pasi('height')

    def menu_bar(self):
        layout = sg.Menu(
            [["&File", ["&Job Planner", "&Shooting Interface", "&Change Theme", ['&Dark', '&Light']]]],
            tearoff=False,
            key="main_menu")
        return layout

    def main_layout(self):
        layout = [
            [self.menu_bar(), sg.Text('', size=(0,5))],
            [sg.Column(layout=
            [
                [sg.Image(f"{resources}/logo.png", pad=(0,10))],

            ]
            , justification="center", )]]

        return layout

class JobPlannerLayout:
    width = config.pasi('width')
    height = config.pasi('width')

    def menu_bar(self):
        layout = sg.Menu([["&Help"]],
                         tearoff=False,
                         key="main_menu")
        return layout

    def main_layout(self):
        layout = [[
            self.menu_bar()
        ]]

        return layout

class ShootingLayout:
    checkmark = u'\u2713'

    def main_menu(self):
        layout = sg.Menu(
            [["&File", ["&View Logs", "&Changed Expected Amount"]]],
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
                                               font='any 16',
                                               key='label_expected_amount')
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
                          border_width=5)
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
                    # image_filename="resources/button.png",
                    # image_subsample=4,
                    # focus=False,
                    border_width=5)
            ]
        ])

        return layout

    def column2_layout(self):
        layout = sg.Column(layout=[[
            sg.Frame('', border_width=0, layout=self.anticipated_layout()),
            sg.Frame('', border_width=0, layout=self.expected_layout())
        ],
        [
            sg.Listbox(values=[],
                        size=(20, 20),
                        key='switch_list',
                        enable_events=True)
        ]])
        return layout

    def debug_area(self):
        width = int(config.pasi('width')) / 17
        height = int(config.pasi('height')) / 100
        print(width, height)
        layout = sg.Multiline(default_text='',
                              size=(int(width), height),
                              key="debug_area",
                              do_not_clear=True)
        return layout

    def main_layout(self):
        layout = [[
            self.main_menu(),
            self.column1_layout(),
            self.column2_layout()
        ], [self.debug_area()]]
        return layout
