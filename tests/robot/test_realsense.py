import argparse
import sys

sys.path.append("./devastator")

from robot import realsense

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=realsense.HOST)
    parser.add_argument("--port", type=int, default=realsense.PORT)
    args = parser.parse_args()

    camera = realsense.D435i(host=args.host, port=args.port)
    camera.run()