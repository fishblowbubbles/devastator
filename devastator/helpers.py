import cv2

from robot import realsense
from vision.helpers import darknet_detect


def darknet_livestream(net, meta, annotator, thresh=0.05, fps=24):
    delay = int(100 / fps)
    while True:
        rgbd = realsense.get_frames()
        darknet_detect(net, meta, rgbd, annotator)
        if cv2.waitKey(delay) == ord("q"):
            break
    cv2.destroyAllWindows()
