import argparse

# from app import ?
from robot import controller, realsense, respeaker, romeo
# from sound import ?
# from vision import ?


HOST = "127.0.0.1"
PORT = 7777


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    if args.robot:
        d435i = realsense.D435i()
        # respeaker = respeaker.MicArrayV2()
    if args.app:
        # app = app.App()
        xpad = controller.XboxOneSPad()
