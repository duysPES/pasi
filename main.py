from pysrc.gui import Pasi
from screeninfo import get_monitors
from pysrc import config
import argparse


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

    elif (h, w) == (1080, 1920):
        gw = 600
        gh = 900
    else:
        gw = 360
        gh = 640

    if (h, w) == (0, 0):
        return False
    else:
        config.update("pasi", 'width', gw)
        config.update('pasi', 'height', gh)

        # config.update("PASI", "width", str(gw), dump=True)
        # config.update("PASI", "height", str(gh), dump=True)


def main():
    screen_size_setup()
    gui = Pasi()
    gui.loop()
    print("..done..")


if __name__ == "__main__":
    main()
