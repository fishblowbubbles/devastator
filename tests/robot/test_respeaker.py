import argparse
import sys

sys.path.append("./devastator")

from robot import respeaker

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=respeaker.BUFFER_SIZE_IN_SECONDS)
    parser.add_argument("--host", default=respeaker.HOST)
    parser.add_argument("--port", type=int, default=respeaker.PORT)
    args = parser.parse_args()

    microphone = respeaker.ReSpeaker(seconds=args.seconds, host=args.host, port=args.port)
    microphone.run()