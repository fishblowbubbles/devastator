import time

import cv2

import robot.realsense as realsense
import robot.respeaker as respeaker
from robot.helpers import get_data
from sound.helpers import vokaturi_detect
from vision.helpers import darknet_detect


def darknet_livestream(net, meta, annotator, thresh=0.05, fps=24):
    delay = int(100 / fps)
    while True:
        rgbd = get_data(realsense.HOST, realsense.PORT)
        darknet_detect(net, meta, rgbd, annotator)
        if cv2.waitKey(delay) == ord("q"): break
    cv2.destroyAllWindows()


def vokaturi_livestream(filename=".tmp/audio.wav", rate=respeaker.RATE, interval=0.5):
    while True:
        samples = get_data(respeaker.HOST, respeaker.PORT)
        vokaturi_detect(samples, rate, filename)
        time.sleep(interval)
