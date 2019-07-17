import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2 as cv
import pyrealsense2 as rs
import numpy as np
import timeit
from openvino.inference_engine import IENetwork, IEPlugin



pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = config.resolve(pipeline)
pipeline.start(config)

model_xml = '/opt/intel/openvino/deployment_tools/tools/model_downloader/Transportation/object_detection/face/pruned_mobilenet_reduced_ssd_shared_weights/dldt/face-detection-adas-0001-fp16.xml'
model_bin = '/opt/intel/openvino/deployment_tools/tools/model_downloader/Transportation/object_detection/face/pruned_mobilenet_reduced_ssd_shared_weights/dldt/face-detection-adas-0001-fp16.bin'

cpu_extension = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so'
device = 'MYRIAD'

plugin = IEPlugin(device=device, plugin_dirs=None)
if cpu_extension and 'CPU' in device:
    plugin.add_cpu_extension(cpu_extension)

net = IENetwork(model=model_xml, weights=model_bin)
#plugin.set_initial_affinity(net)

if plugin.device == "CPU":
    supported_layers = plugin.get_supported_layers(net)
    not_supported_layers = [l for l in net.layers.keys() if l not in supported_layers]
    if len(not_supported_layers) != 0:
        print("Following layers are not supported by the plugin for specified device {}:\n {}".
              format(plugin.device, ', '.join(not_supported_layers)))
        print("Please try to specify cpu extensions library path in sample's command line parameters using -l "
              "or --cpu_extension command line argument")
        sys.exit(1)

input_blob = next(iter(net.inputs))

net.batch_size = 1

n, c, h, w = net.inputs[input_blob].shape

exec_net = plugin.load(network=net, num_requests=2)

start = timeit.default_timer()
num_frames = 0
while True:

    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    if not color_frame:
        continue
    original_image = np.array(color_frame.get_data())

    in_frame = cv.resize(original_image, (w, h))
    in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
    in_frame = in_frame.reshape((n, c, h, w))


    out = exec_net.infer({'data': in_frame})
    
    crops = []
    for detection in out['detection_out'][0][0]:
        confidence = float(detection[2])
        xmin = int(detection[3] * original_image.shape[1])
        ymin = int(detection[4] * original_image.shape[0])
        xmax = int(detection[5] * original_image.shape[1])
        ymax = int(detection[6] * original_image.shape[0])
        if confidence > 0.5:
            cv.rectangle(original_image, (xmin, ymin), (xmax, ymax), color=(0, 255, 0))
        crops.append(original_image[ymin: ymax, xmin: xmax])
    
    cv.imshow('Video', original_image)
    num_frames = num_frames + 1
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

print(num_frames/(timeit.default_timer() - start), "frames per second")
video_capture.release()
cv.destroyAllWindows()

