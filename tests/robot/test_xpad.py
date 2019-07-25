import argparse
import sys

sys.path.append("./devastator")

from robot import romeo, xpad

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-name", default=xpad.DEVICE_NAME)
    parser.add_argument("--target-host", default=romeo.HOST)
    parser.add_argument("--target-port", type=int, default=romeo.PORT)
    args = parser.parse_args()

    controller = xpad.XPad(target_host=args.target_host,
                           target_port=args.target_port,
                           device_name=args.device_name)
    controller.run()
