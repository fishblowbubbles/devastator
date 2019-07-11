import cv2

import robot.realsense as realsense
from robot.helpers import get_data
from vision.helpers import darknet_detect


def darknet_livestream(net, meta, annotator, thresh=0.05, fps=24):
    delay = int(100 / fps)
    while True:
        rgbd = get_frames(realsense.HOST, realsense.PORT)
        darknet_detect(net, meta, rgbd, annotator)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()
