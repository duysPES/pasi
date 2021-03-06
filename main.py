from pysrc.gui import Pasi
from screeninfo import get_monitors
from pysrc import config
import argparse


def screen_size_setup():

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
        return True


parser = argparse.ArgumentParser()
parser.add_argument('--height',
                    metavar='N',
                    type=int,
                    help="height of main gui",
                    default=640)
parser.add_argument('--width',
                    metavar='N',
                    type=int,
                    help="width of main gui",
                    default=360)


def main():
    # if not screen_size_setup():
    #     print("Unable to setup gui dimensions, wrong screen size")
    #     return
    args = parser.parse_args()
    width, height = args.width, args.height
    config.update("pasi", 'width', width)
    config.update('pasi', 'height', height)
    gui = Pasi()
    gui.loop()
    print("..done..")


if __name__ == "__main__":
    main()
