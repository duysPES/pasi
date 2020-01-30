from pysrc.gui import Pasi
from screeninfo import get_monitors
from pysrc import config


def screen_size_setup():
    h, w = 0, 0
    monitors = get_monitors()
    for m in monitors:
        if h < m.height:
            h = m.height
        if w < m.width:
            w = m.width

    if (h, w) == (2160, 3840):
        gw = 800
        gh = 1200

    elif (h, w) == (1920, 1080):
        gw = 550
        gh = 700

    if (h, w) == (0, 0):
        return False
    else:
        config.update("PASI", "width", str(gw), dump=True)
        config.update("PASI", "height", str(gh), dump=True)


if __name__ == "__main__":
    screen_size_setup()
    gui = Pasi()
    gui.loop()

    print("..done..")
