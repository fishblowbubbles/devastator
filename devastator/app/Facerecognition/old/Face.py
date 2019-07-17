import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2 as cv
import pyrealsense2 as rs
import numpy as np

net = cv.dnn.readNet('face-detection-adas-0001.bin', 'face-detection-adas-0001.xml')

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = config.resolve(pipeline)
pipeline.start(config)

while 1:
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    if not color_frame:
        continue
    frame = np.array(color_frame.get_data())

    blob = cv.dnn.blobFromImage(frame, size=(672, 384))
    net.setInput(blob)
    out = net.forward()

    for detection in out.reshape(-1, 7):
        confidence = float(detection[2])
        xmin = int(detection[3] * frame.shape[1])
        ymin = int(detection[4] * frame.shape[0])
        xmax = int(detection[5] * frame.shape[1])
        ymax = int(detection[6] * frame.shape[0])

        if confidence > 0.5:
            cv.rectangle(frame, (xmin, ymin), (xmax, ymax), color=(0, 255, 0))

    cv.imshow('OpenVINO face detection', frame)
