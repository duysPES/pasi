import PySimpleGUI as sg

FIRING_BUTTONS = {
    "Active": ("#1a1a1a", "#ffbb4c"),
    "Inactive": ("#eeffff", "#8d8d8d")
}

__DEFAULT_FONT = ('fixedsys', 9)
__DEFAULT_PADDING = (5, 5)

__LOOK_AND_FEEL_TABLE = {
    "Dark": {
        "Background": "#1a1a1a",
        "Text": "#eeffff",
        "Input": "#424242",
        "Text_Input": "#eeffff",
        "Scroll": "#ed7b3e",
        "Button": FIRING_BUTTONS['Inactive'],
        "Progress": sg.DEFAULT_PROGRESS_BAR_COLOR,
        "Border": 1,
        "Slider_Depth": 0,
        "Progress_Depth": 0
    }
}


def set_dark():
    colors = __LOOK_AND_FEEL_TABLE["Dark"]
    sg.SetOptions(background_color=colors['Background'],
                  text_element_background_color=colors['Background'],
                  element_background_color=colors['Background'],
                  text_color=colors['Text'],
                  input_elements_background_color=colors['Input'],
                  button_color=colors['Button'],
                  progress_meter_color=colors['Progress'],
                  border_width=colors['Border'],
                  slider_border_width=colors['Slider_Depth'],
                  progress_meter_border_depth=colors['Progress_Depth'],
                  scrollbar_color=(colors['Scroll']),
                  element_text_color=colors['Text'],
                  input_text_color=colors['Text_Input'],
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
