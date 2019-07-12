import argparse
import sys

sys.path.append("./devastator")

from robot import romeo

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=romeo.HOST)
    parser.add_argument("--port", type=int, default=romeo.PORT)
    args = parser.parse_args()

    motors = romeo.Romeo(host=args.host, port=args.port)
    motors.run()