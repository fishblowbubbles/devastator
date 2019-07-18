import argparse
import sys
from multiprocessing import Process

from robot.helpers import get_data
from robot.realsense import D435i
from robot.respeaker import ReSpeaker
from robot.romeo import Romeo
from robot.xpad import XPad
from sound.helpers import vokaturi_func

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    args = parser.parse_args()

    if args.robot:
        # load the hardware
        devices = {"realsense": D435i(),
                   "respeaker": ReSpeaker(),
                   "romeo": Romeo()}
        # load your algorithms
    elif args.app:
        devices = {"xpad": XPad()}
    else:
        sys.exit()

    processes = {}

    for name, device in devices.items():
        processes[name] = Process(target=device.run)

    for name, device in processes.items():
        device.start()

    """
    while True:
        get_frame()
        yolo_detect()
        acoular_detect()
        send_to_app()
    """
