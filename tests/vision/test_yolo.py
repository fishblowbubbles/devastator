import sys, os
sys.path.append(".")

import argparse
import pickle
import socket
from copy import deepcopy
from time import sleep

import cv2
import matplotlib.pyplot as plt
import numpy as np

import devastator.robot.realsense as realsense
import devastator.vision.darknet as darknet
import devastator.vision.helpers as vision


N_CLASSES = 8
CMAP = plt.get_cmap("rainbow")
COLORS = [CMAP(i) for i in np.linspace(0, 1, N_CLASSES)]

PATH2WEIGHTS = "devastator/vision/darknet/backup/custom_8.weights"
PATH2NAMES = "devastator/vision/darknet/data/custom_8.names"
PATH2DATA = "devastator/vision/darknet/cfg/custom_8.data"
PATH2CFG = "devastator/vision/darknet/cfg/custom_8.cfg"

FPS = 24
THRESH = 0.1


def load_names(path):
    print(os.path.abspath(path))
    names = []
    with open(path, "r") as file:
        lines = file.read()
        lines = lines.strip().split("\n")
        for line in lines:
            names.append(line)
    return names


def add_circles(img, input_map=vision.INPUT_MAP):
    for point in input_map:
        cv2.circle(img, tuple(point), 5, (0, 0, 255), -1)


def add_patches(r, img, depth, colors=COLORS):
    for label, confidence, coords in r:
        x, y, width, height = coords
        label = label.decode("utf-8")
        color = colors[names.index(label)][:3]
        color = [int(x * 255) for x in color]
        distance = round(depth[int(y), int(x)] / 1000, 2)
        s = "{} (Conf.: {}, Dist.: {} m)".format(label, round(confidence, 2), distance)
        font = cv2.FONT_HERSHEY_DUPLEX
        x1, y1, x2, y2 = (
            int(x - width / 2),
            int(y - height / 2),
            int(x + width / 2),
            int(y + height / 2),
        )
        cv2.putText(img, s, (x1 + 5, y1 - 5), font, 0.5, color, 1, cv2.LINE_AA)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.circle(img, (int(x), int(y)), 5, color, -1)


def predict(net, data, thresh=THRESH):
    rgbd = realsense.get_frame()
    rgb, d = rgbd[:, :, :3].astype(np.uint8), rgbd[:, :, 3]
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    cv2.imwrite(".tmp/frame.jpg", rgb)
    predictions = darknet.detect(net, data, ".tmp/frame.jpg".encode("ascii"), thresh=0.1)
    add_patches(predictions, rgb, d)
    cv2.imshow("darknet", rgb)


def livestream(net, data, fps=FPS):
    delay = int(100 / fps)
    while True:
        predict(net, data)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", action="store_true")
    parser.add_argument("--fps", type=int, default=FPS)
    args = parser.parse_args()
    names = load_names(PATH2NAMES)
    net = darknet.load_net(PATH2CFG.encode("ascii"), PATH2WEIGHTS.encode("ascii"), 0)
    data = darknet.load_meta(PATH2DATA.encode("ascii"))
    if args.video:
        livestream(net, data, args.fps)
    else:
        predict(net, data)
        cv2.waitKey(0)
