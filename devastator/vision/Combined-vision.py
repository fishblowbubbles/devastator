from __future__ import print_function, division
import pyrealsense2 as rs
import logging
import os
import sys
from argparse import ArgumentParser, SUPPRESS
from math import exp as exp
from time import time
import numpy as np
import pickle
import socket

sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')

import cv2
from openvino.inference_engine import IENetwork, IEPlugin

logging.basicConfig(format="[ %(levelname)s ] %(message)s", level=logging.INFO, stream=sys.stdout)
log = logging.getLogger()

#Arguments Parser, I've removed a ton of arguments I did not use from the original
def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument("-i", "--input", help="Path to a image/video file. (Specify 'cam' to work with "
                                            "default webcamera, 'rs' to work with realsense camera, 'server' to grab from server hosting realsense images. default 'server')", default="server", type=str)
    args.add_argument("-pp", "--plugin_dir", help="Optional. Path to a plugin folder", type=str, default=None)
    args.add_argument("-t_yolo", "--yolo_threshold", help="Optional. Probability threshold for detections filtering of YOLO model. default 0.1",
                      default=0.1, type=float)
    args.add_argument("-t_face", "--face_threshold", help="Optional. Probability threshold for detections filtering of face detection model. default 0.5",
                      default=0.5, type=float)
    args.add_argument("-iout", "--iou_threshold", help="Optional. Intersection over union threshold for overlapping "
                                                       "detections filtering. default 0.4", default=0.4, type=float)
    return parser


class YoloV3Params:
    # ------------------------------------------- Extracting layer parameters ------------------------------------------
    # Magic numbers are copied from yolo samples
    def __init__(self, param, side):
        self.num = 3 if 'num' not in param else len(param['mask'].split(',')) if 'mask' in param else int(param['num'])
        self.coords = 4 if 'coords' not in param else int(param['coords'])
        self.classes = 8 #if 'classes' not in param else int(param['classes'])
        self.anchors = [10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0,
                        198.0,
                        373.0, 326.0] if 'anchors' not in param else [float(a) for a in param['anchors'].split(',')]
        self.side = side
        if self.side == 13:
            self.anchor_offset = 2 * 3
        elif self.side == 26:
            self.anchor_offset = 2 * 0
        else:
            assert False, "Invalid output size. Only 13, 26 and 52 sizes are supported for output spatial dimensions"

def entry_index(side, coord, classes, location, entry):
    side_power_2 = side ** 2
    n = location // side_power_2
    loc = location % side_power_2
    return int(side_power_2 * (n * (coord + classes + 1) + entry) + loc)


def scale_bbox(x, y, h, w, class_id, confidence, h_scale, w_scale):
    xmin = int((x - w / 2) * w_scale)
    ymin = int((y - h / 2) * h_scale)
    xmax = int(xmin + w * w_scale)
    ymax = int(ymin + h * h_scale)
    return dict(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, class_id=class_id, confidence=confidence)


def parse_yolo_region(blob, resized_image_shape, original_im_shape, params, threshold):
    # ------------------------------------------ Validating output parameters ------------------------------------------
    _, _, out_blob_h, out_blob_w = blob.shape
    assert out_blob_w == out_blob_h, "Invalid size of output blob. It sould be in NCHW layout and height should " \
                                     "be equal to width. Current height = {}, current width = {}" \
                                     "".format(out_blob_h, out_blob_w)

    # ------------------------------------------ Extracting layer parameters -------------------------------------------
    orig_im_h, orig_im_w = original_im_shape
    resized_image_h, resized_image_w = resized_image_shape
    objects = list()
    predictions = blob.flatten()
    side_square = params.side * params.side

    # ------------------------------------------- Parsing YOLO Region output -------------------------------------------
    for i in range(side_square):
        row = i // params.side
        col = i % params.side
        for n in range(params.num):
            obj_index = entry_index(params.side, params.coords, params.classes, n * side_square + i, params.coords)
            scale = predictions[obj_index]
            if scale < threshold:
                continue
            box_index = entry_index(params.side, params.coords, params.classes, n * side_square + i, 0)
            x = (col + predictions[box_index + 0 * side_square]) / params.side * resized_image_w
            y = (row + predictions[box_index + 1 * side_square]) / params.side * resized_image_h
            # Value for exp is very big number in some cases so following construction is using here
            try:
                w_exp = exp(predictions[box_index + 2 * side_square])
                h_exp = exp(predictions[box_index + 3 * side_square])
            except OverflowError:
                continue
            w = w_exp * params.anchors[params.anchor_offset + 2 * n]
            h = h_exp * params.anchors[params.anchor_offset + 2 * n + 1]
            for j in range(params.classes):
                class_index = entry_index(params.side, params.coords, params.classes, n * side_square + i,
                                          params.coords + 1 + j)
                confidence = scale * predictions[class_index]
                if confidence < threshold:
                    continue
                objects.append(scale_bbox(x=x, y=y, h=h, w=w, class_id=j, confidence=confidence,
                                          h_scale=orig_im_h / resized_image_h, w_scale=orig_im_w / resized_image_w))
    return objects


def intersection_over_union(box_1, box_2):
    width_of_overlap_area = min(box_1['xmax'], box_2['xmax']) - max(box_1['xmin'], box_2['xmin'])
    height_of_overlap_area = min(box_1['ymax'], box_2['ymax']) - max(box_1['ymin'], box_2['ymin'])
    if width_of_overlap_area < 0 or height_of_overlap_area < 0:
        area_of_overlap = 0
    else:
        area_of_overlap = width_of_overlap_area * height_of_overlap_area
    box_1_area = (box_1['ymax'] - box_1['ymin']) * (box_1['xmax'] - box_1['xmin'])
    box_2_area = (box_2['ymax'] - box_2['ymin']) * (box_2['xmax'] - box_2['xmin'])
    area_of_union = box_1_area + box_2_area - area_of_overlap
    if area_of_union == 0:
        return 0
    return area_of_overlap / area_of_union

def recv_object(client):
    packets = []
    while True:
        packet = client.recv(1024)
        if not packet:
            break
        packets.append(packet)
    object = pickle.loads(b"".join(packets))
    return object


def get_frame(HOST, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        rgbd = recv_object(client)
    return rgbd


def main():
    args = build_argparser().parse_args()

    #PARAMS
    HOST = "127.0.0.1"
    PORT = 4444
    yolo_xml = './TinyV2.xml'
    yolo_bin = './TinyV2.bin'
    face_xml = './face-detection-adas-0001-fp16.xml'
    face_bin = './face-detection-adas-0001-fp16.bin'
    labels = './custom.names'
    cpu_extension = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so'
    face_device = 'MYRIAD'
    yolo_device = 'GPU'


    # ------------- 1. Plugin initialization for specified device and load extensions library if specified -------------
    yolo_plugin = IEPlugin(device=yolo_device, plugin_dirs=args.plugin_dir)
    if 'CPU' in yolo_device:
        yolo_plugin.add_cpu_extension(args.cpu_extension)

    face_plugin = IEPlugin(device=face_device, plugin_dirs=None)
    if 'CPU' in face_device:
        face_plugin.add_cpu_extension(cpu_extension)


    # -------------------- 2. Reading the IR generated by the Model Optimizer (.xml and .bin files) --------------------
    log.info("Loading network files:\n\t{}\n\t{}".format(yolo_xml, yolo_bin))
    yolonet = IENetwork(model=yolo_xml, weights=yolo_bin)
    facenet = IENetwork(model=face_xml, weights=face_bin)

    # ---------------------------------- 3. Load CPU extension for support specific layer ------------------------------
    if yolo_plugin == "CPU":
        supported_layers = yolo_plugin.get_supported_layers(net)
        not_supported_layers = [l for l in yolonet.layers.keys() if l not in supported_layers]
        if len(not_supported_layers) != 0:
            log.error("Following layers are not supported by the plugin for specified device {}:\n {}".
                      format(yolo_plugin.device, ', '.join(not_supported_layers)))
            log.error("Please try to specify cpu extensions library path in sample's command line parameters using -l "
                      "or --cpu_extension command line argument")
            sys.exit(1)

    if face_plugin == "CPU":
        supported_layers = face_plugin.get_supported_layers(net)
        not_supported_layers = [l for l in facenet.layers.keys() if l not in supported_layers]
        if len(not_supported_layers) != 0:
            log.error("Following layers are not supported by the plugin for specified device {}:\n {}".
                      format(face_plugin.device, ', '.join(not_supported_layers)))
            log.error("Please try to specify cpu extensions library path in sample's command line parameters using -l "
                      "or --cpu_extension command line argument")
            sys.exit(1)

    assert len(yolonet.inputs.keys()) == 1, "Sample supports only Tiny YOLO V3 based single input topologies"
    assert len(yolonet.outputs) == 2, "Sample supports only Tiny YOLO V3 based double output topologies"

    # ---------------------------------------------- 4. Preparing inputs -----------------------------------------------
    log.info("Preparing inputs")
    yolo_input_blob = next(iter(yolonet.inputs))

    #  Defaulf batch_size is 1
    yolonet.batch_size = 1

    # Read and pre-process input images
    n1, c1, h1, w1 = yolonet.inputs[yolo_input_blob].shape

    with open(labels, 'r') as f:
        labels_map = [x.strip() for x in f]

    face_input_blob = next(iter(facenet.inputs))

    facenet.batch_size = 1

    n2, c2, h2, w2 = facenet.inputs[face_input_blob].shape



###############################################################################################################
    if args.input == "rs":
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        profile = config.resolve(pipeline)
        pipeline.start(config)
        number_input_frames = 5
    elif args.input == "server":
        number_input_frames = 5
    else:
        input_stream = 0 if args.input == "cam" else args.input
        cap = cv2.VideoCapture(input_stream)
        number_input_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    is_async_mode = True
    number_input_frames = 1 if number_input_frames != -1 and number_input_frames < 0 else number_input_frames

    wait_key_code = 1

    # Number of frames in picture is 1 and this will be read in cycle. Sync mode is default value for this case
    if number_input_frames != 1:
        if args.input == "rs":
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            frame = np.array(color_frame.get_data())
            ret = True
        elif args.input == "server":
            rgbd = get_frame(HOST, PORT)
            rgb, d = rgbd[:, :, :3].astype(np.uint8), rgbd[:, :, 3]
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            frame = np.array(rgb)
            ret = True
        else:
            ret, frame = cap.read()
    else:
        is_async_mode = False
        wait_key_code = 0

    # ----------------------------------------- 5. Loading model to the plugin -----------------------------------------
    log.info("Loading model to the plugin")
    exec_yolo_net = yolo_plugin.load(network=yolonet, num_requests=2)
    exec_face_net = face_plugin.load(network=facenet, num_requests=2)

    cur_request_id = 0
    next_request_id = 1
    render_time = 0
    parsing_time = 0
    print(args.input)

    # ----------------------------------------------- 6. Doing inference -----------------------------------------------
    print("To close the application, press 'ESC' with focus on the output window")
    while True:
        # Here is the first asynchronous point: in the Async mode, we capture frame to populate the NEXT infer request
        # in the regular mode, we capture frame to the CURRENT infer request
        if args.input == "rs":
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            next_frame = np.array(color_frame.get_data())
            ret = True
        elif args.input == "server":
            rgbd = get_frame(HOST, PORT)
            rgb, d = rgbd[:, :, :3].astype(np.uint8), rgbd[:, :, 3]
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            next_frame = np.array(rgb)
            ret = True
        else:
            if is_async_mode:
                ret, next_frame = cap.read()
            else:
                ret, frame = cap.read()

        if not ret:
            break

        if is_async_mode:
            request_id = next_request_id
        else:
            request_id = cur_request_id



        if is_async_mode:
            yolo_in = cv2.resize(next_frame, (w1, h1))
            face_in = cv2.resize(next_frame, (w2, h2))
        else:
            yolo_in = cv2.resize(frame, (w1, h1))
            face_in = cv2.resize(frame, (w2, h2))

##########################################################################################################################

        # resize input_frame to network size
        yolo_in = yolo_in.transpose((2, 0, 1))  # Change data layout from HWC to CHW
        yolo_in = yolo_in.reshape((n1, c1, h1, w1))
    
        face_in = face_in.transpose((2, 0, 1))  # Change data layout from HWC to CHW
        face_in = face_in.reshape((n2, c2, h2, w2))

        # Start inference
        start_time = time()
        exec_yolo_net.start_async(request_id=request_id, inputs={yolo_input_blob: yolo_in})
        
        det_time = time() - start_time
        
        # Collecting object detection results
        start_time = time()
        faces = exec_face_net.infer({'data': face_in})
        objects = list()
        if exec_yolo_net.requests[cur_request_id].wait(-1) == 0:
            output = exec_yolo_net.requests[cur_request_id].outputs
            

            for layer_name, out_blob in output.items():
                layer_params = YoloV3Params(yolonet.layers[layer_name].params, out_blob.shape[2])
                objects += parse_yolo_region(out_blob, yolo_in.shape[2:],
                                         frame.shape[:-1], layer_params,
                                         args.yolo_threshold)
        parsing_time = time() - start_time

        # Collecting face detection results
#------------------- Results of face detection -------------------------------------
        crops = []
        for detection in faces['detection_out'][0][0]:
            confidence = float(detection[2])
            xmin = int(detection[3] * frame.shape[1])
            ymin = int(detection[4] * frame.shape[0])
            xmax = int(detection[5] * frame.shape[1])
            ymax = int(detection[6] * frame.shape[0])
            if confidence > args.face_threshold:
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color=(0, 255, 0))
                cv2.putText(frame,
                        "# face " + str(round(confidence * 100, 1)) + ' %',
                        (xmin, ymin - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 255, 0), 1)
            crops.append(frame[ymin: ymax, xmin: xmax])
        
        # Filtering overlapping boxes with respect to the --iou_threshold CLI parameter
        for i in range(len(objects)):
            if objects[i]['confidence'] == 0:
                continue
            for j in range(i + 1, len(objects)):
                if intersection_over_union(objects[i], objects[j]) > args.iou_threshold:
                    objects[j]['confidence'] = 0

        # Drawing objects with respect to the --yolo_threshold CLI parameter
        objects = [obj for obj in objects if obj['confidence'] >= args.yolo_threshold]

#------------------- Results of yolo detection -------------------------------------
        origin_im_size = frame.shape[:-1]
        for obj in objects:
            # Validation bbox of detected object
            if obj['xmax'] > origin_im_size[1] or obj['ymax'] > origin_im_size[0] or obj['xmin'] < 0 or obj['ymin'] < 0:
                continue
            color = (int(min(obj['class_id'] * 12.5, 255)),
                     min(obj['class_id'] * 7, 255), min(obj['class_id'] * 5, 255))
            det_label = labels_map[obj['class_id']] if labels_map and len(labels_map) >= obj['class_id'] else \
                str(obj['class_id'])
            print(det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %')
            cv2.rectangle(frame, (obj['xmin'], obj['ymin']), (obj['xmax'], obj['ymax']), color, 2)
            cv2.putText(frame,
                        "#" + det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %',
                        (obj['xmin'], obj['ymin'] - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)

        # Draw performance stats over frame
        inf_time_message = "Inference time: N\A for async mode" if is_async_mode else \
            "Inference time: {:.3f} ms".format(det_time * 1e3)
        render_time_message = "OpenCV rendering time: {:.3f} ms".format(render_time * 1e3)
        async_mode_message = "Async mode is on. Processing request {}".format(cur_request_id) if is_async_mode else \
            "Async mode is off. Processing request {}".format(cur_request_id)
        parsing_message = "YOLO parsing time is {:.3f}".format(parsing_time * 1e3)

        cv2.putText(frame, inf_time_message, (15, 15), cv2.FONT_HERSHEY_COMPLEX, 0.5, (200, 10, 10), 1)
        cv2.putText(frame, render_time_message, (15, 45), cv2.FONT_HERSHEY_COMPLEX, 0.5, (10, 10, 200), 1)
        cv2.putText(frame, async_mode_message, (10, int(origin_im_size[0] - 20)), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                    (10, 10, 200), 1)
        cv2.putText(frame, parsing_message, (15, 30), cv2.FONT_HERSHEY_COMPLEX, 0.5, (10, 10, 200), 1)

        start_time = time()
        cv2.imshow("DetectionResults", frame)
        render_time = time() - start_time

        if is_async_mode:
            cur_request_id, next_request_id = next_request_id, cur_request_id
            frame = next_frame

        key = cv2.waitKey(wait_key_code)

        # ESC key
        if key == 27:
            print("Exiting")
            break
        # Tab key
        if key == 9:
            exec_yolo_net.requests[cur_request_id].wait()
            is_async_mode = not is_async_mode
            log.info("Switched to {} mode".format("async" if is_async_mode else "sync"))

    cv2.destroyAllWindows()


if __name__ == '__main__':
    sys.exit(main() or 0)
