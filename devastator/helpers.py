import cv2
import numpy as np

import devastator.robot.realsense as realsense
import devastator.vision.darknet as darknet
from devastator.vision.helpers import add_patches


def split_rgbd(rgbd):
    rgb, d = rgbd[:, :, :3].astype(np.uint8), rgbd[:, :, 3]
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    return rgb, d


def predict(net, meta, names, colors, thresh=0.05, show=True):
    rgbd = realsense.get_frames()
    rgb, d = split_rgbd(rgbd)
    cv2.imwrite(".tmp/frame.jpg", rgb)
    preds = darknet.detect(net, meta, ".tmp/frame.jpg".encode("ascii"), thresh=thresh)
    if show:
        add_patches(preds, rgb, d, names, colors)
        cv2.imshow("darknet", rgb)
    return preds


def livestream(net, meta, names, colors, thresh=0.05, fps=24):
    delay = int(100 / fps)
    while True:
        predict(net, meta, names, colors)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()
