import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2 as cv
import pyrealsense2 as rs
import numpy as np
import time

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = config.resolve(pipeline)
pipeline.start(config)

x = 0
while True:

    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    if not color_frame:
        continue
    original_image = np.array(color_frame.get_data())

    x = x +1
    if x % 1000000 == 0:
        np.save("capture/image_" + str(x//1000000), original_image)
    cv.imshow('Video', original_image)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

print(num_frames/(timeit.default_timer() - start), "frames per second")
video_capture.release()
cv.destroyAllWindows()
