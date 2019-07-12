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
        devices = { # "realsense": D435i(),
                   "respeaker": ReSpeaker(),
                   "romeo": Romeo()}
    elif args.app:
        devices = {"xpad": XPad()}
    else:
        sys.exit()

    processes = {}
    for name, device in devices.items():
        processes[name] = Process(target=device.run)
    for name, device in processes.items():
        print("Starting {} ... ".format(name), end="")
        device.start()
        print("ready")
