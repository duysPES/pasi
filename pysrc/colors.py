"""
Holds constants and variables that deal with the overall look
and feel of the graphical UX for PASI
"""

import PySimpleGUI as sg

FIRING_BUTTONS = {
    "dark": {
        "active": ("#1a1a1a", "#ffbb4c"),
        "inactive": ("#eeffff", "#8d8d8d")
    },
    "light": {
        "active": ("#1a1a1a", "#ffbb4c"),
        "inactive": ("#eeffff", "#8d8d8d")
    }
}

__DEFAULT_FONT = ('fixedsys', 9)
__DEFAULT_PADDING = (5, 5)

__LOOK_AND_FEEL_TABLE = {
    "dark": {
        "background": "#1a1a1a",
        "text": "#eeffff",
        "input": "#424242",
        "text_input": "#eeffff",
        "scroll": "#ed7b3e",
        "button": FIRING_BUTTONS['dark']['inactive'],
        "progress": sg.DEFAULT_PROGRESS_BAR_COLOR,
        "border": 1,
        "slider_depth": 0,
        "progress_depth": 0
    }
}


def set_dark():
    """
    changes elements within pysimplegui to a dark
    theme
    """
    colors = __LOOK_AND_FEEL_TABLE["dark"]
    sg.SetOptions(background_color=colors['background'],
                  text_element_background_color=colors['background'],
                  element_background_color=colors['background'],
                  text_color=colors['text'],
                  input_elements_background_color=colors['input'],
                  button_color=colors['button'],
                  progress_meter_color=colors['progress'],
                  border_width=colors['border'],
                  slider_border_width=colors['slider_depth'],
                  progress_meter_border_depth=colors['progress_depth'],
                  scrollbar_color=(colors['scroll']),
                  element_text_color=colors['text'],
                  input_text_color=colors['text_input'],
                  element_padding=__DEFAULT_PADDING,
                  font=__DEFAULT_FONT)


if __name__ == "__main__":
    import sys
    args = sys.argv
    theme = args[1]
    set_dark()

    layout = [[sg.Text("Hello World")], [sg.Multiline("Enter Here")],
              [
                  sg.Combo([1, 2, 3, 4], size=(10, 5)),
                  sg.Listbox([x for x in range(20)], size=(10, 10))
              ], [sg.Submit(), sg.Exit()]]

    window = sg.Window(f"showing {theme}", layout=layout)

    while True:
        event, value = window.read()

        if event in (None, "Exit"):
            break
