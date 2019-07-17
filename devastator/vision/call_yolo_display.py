from __future__ import print_function, division

import os
import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
from argparse import ArgumentParser, SUPPRESS
from math import exp as exp
from time import time
import numpy as np
import cv2
import socket
import pickle
import math
from PIL import Image
from openvino.inference_engine import IENetwork, IEPlugin




def build_argparser():
    parser = ArgumentParser(add_help=False)
    args = parser.add_argument_group('Options')
    args.add_argument('-h', '--help', action='help', default=SUPPRESS, help='Show this help message and exit.')
    args.add_argument("-i", "--input", help="Required. Path to a image/video file. (Specify 'cam' to work with "
                                            "camera)", type=str, default='server')
    args.add_argument("-pp", "--plugin_dir", help="Optional. Path to a plugin folder", type=str, default=None)
    args.add_argument("-t", "--prob_threshold", help="Optional. Probability threshold for detections filtering",
                      default=0.2, type=float)
    args.add_argument("-iout", "--iou_threshold", help="Optional. Intersection over union threshold for overlapping "
                                                       "detections filtering", default=0.4, type=float)
    args.add_argument("-ni", "--number_iter", help="Optional. Number of inference iterations", default=1, type=int)
    args.add_argument("-pc", "--perf_counts", help="Optional. Report performance counters", default=False,
                      action="store_true")

    return parser


class YoloV3Params:
    # ------------------------------------------- Extracting layer parameters ------------------------------------------
    # Magic numbers are copied from yolo samples
    def __init__(self, param, side):
        self.num = 3 if 'num' not in param else len(param['mask'].split(',')) if 'mask' in param else int(param['num'])
        self.coords = 4 if 'coords' not in param else int(param['coords'])
        self.classes = 80 if 'classes' not in param else int(param['classes'])
        self.anchors = [10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0,
                        198.0,
                        373.0, 326.0] if 'anchors' not in param else [float(a) for a in param['anchors'].split(',')]
        self.side = side
        if self.side == 13:
            self.anchor_offset = 2 * 6
        elif self.side == 26:
            self.anchor_offset = 2 * 3
        elif self.side == 52:
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

def load_model(device, labels, model_xml, model_bin, plugin_dir, cpu_extension = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so' ):
    # ------------- 1. Plugin initialization for specified device and load extensions library if specified -------------
    plugin = IEPlugin(device=device, plugin_dirs=plugin_dir)
    if 'CPU' in device:
        plugin.add_cpu_extension(cpu_extension)

    # -------------------- 2. Reading the IR generated by the Model Optimizer (.xml and .bin files) --------------------
    net = IENetwork(model=model_xml, weights=model_bin)

    # ---------------------------------- 3. Load CPU extension for support specific layer ------------------------------
    if plugin.device == "CPU":
        supported_layers = plugin.get_supported_layers(net)
        not_supported_layers = [l for l in net.layers.keys() if l not in supported_layers]
        if len(not_supported_layers) != 0:
            print("Following layers are not supported by the plugin for specified device {}:\n {}".
                      format(plugin.device, ', '.join(not_supported_layers)))
            print("Please try to specify cpu extensions library path in sample's command line parameters using -l "
                      "or --cpu_extension command line argument")
            sys.exit(1)

    assert len(net.inputs.keys()) == 1, "Sample supports only YOLO V3 based single input topologies"
    assert len(net.outputs) == 3, "Sample supports only YOLO V3 based triple output topologies"

    # ---------------------------------------------- 4. Preparing inputs -----------------------------------------------
    input_blob = next(iter(net.inputs))
    #  Defaulf batch_size is 1
    net.batch_size = 1

    # Read and pre-process input images

    return input_blob, net, plugin.load(network=net, num_requests=2)

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

def corners2center(xmin,xmax,ymin,ymax):
    x = (xmin+xmax)/2
    y = (ymin+ymax)/2
    h = ymax - ymin
    w = xmax - xmin
    return x, y, w, h

def diag(box_1):
    dist1 = ((box_1["xmax"] - box_1["xmin"])**2 + (box_1["ymax"] - box_1["ymin"])**2)**0.5
    return dist1

def expected_len(box_1, depth):
    dist = ((depth*math.tan(((box_1["xmax"] - box_1["xmin"])*0.06796)))**2 + (depth*math.tan(((box_1["ymax"] - box_1["ymin"])*0.0806)))**2)**0.5
    return dist

def main():
    args = build_argparser().parse_args()


    #PARAMS
    HOST = "127.0.0.1"
    PORT = 4445

    device = 'GPU'	#GPU
    labels = './custom.names' #set to None if no labels
    cpu_extension = '/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/libcpu_extension_sse4.so'
    model_xml = './YoloV2_18000.xml'
    model_bin = os.path.splitext(model_xml)[0] + ".bin"

    input_blob, net, exec_net = load_model(device, labels, model_xml, model_bin, plugin_dir = None, cpu_extension = cpu_extension)
    
    n, c, h, w = net.inputs[input_blob].shape
    print("Model loaded")

    if labels:
        with open(labels, 'r') as f:
            labels_map = [x.strip() for x in f]
    else:
        labels_map = None

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



    cur_request_id = 0
    next_request_id = 1
    render_time = 0
    parsing_time = 0

    # ----------------------------------------------- 6. Doing inference -----------------------------------------------
    print("To close the application, press 'CTRL+C' or any key with focus on the output window")
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
            d = np.array(d)
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
            in_frame = cv2.resize(next_frame, (w, h))
        else:
            request_id = cur_request_id
            in_frame = cv2.resize(frame, (w, h))


        # resize input_frame to network size
        in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
        in_frame = in_frame.reshape((n, c, h, w))

        # Start inference
        start_time = time()
        exec_net.start_async(request_id=request_id, inputs={input_blob: in_frame})
        det_time = time() - start_time
        # Collecting object detection results
        objects = list()
        if exec_net.requests[cur_request_id].wait(-1) == 0:
            output = exec_net.requests[cur_request_id].outputs

            start_time = time()
            for layer_name, out_blob in output.items():
                layer_params = YoloV3Params(net.layers[layer_name].params, out_blob.shape[2])
                objects += parse_yolo_region(out_blob, in_frame.shape[2:],
                                             frame.shape[:-1], layer_params,
                                             args.prob_threshold)
            parsing_time = time() - start_time

        # Filtering overlapping boxes with respect to the --iou_threshold CLI parameter
        for i in range(len(objects)):
            if objects[i]['confidence'] == 0:
                continue
            for j in range(i + 1, len(objects)):
                if intersection_over_union(objects[i], objects[j]) > args.iou_threshold:
                    objects[j]['confidence'] = 0

        # Drawing objects with respect to the --prob_threshold CLI parameter
        objects = [obj for obj in objects if obj['confidence'] >= args.prob_threshold]
        original_image = frame
        origin_im_size = frame.shape[:-1]
        people = []
        others = []
        for obj in objects:
            # Validation bbox of detected object
            if obj['xmax'] > origin_im_size[1] or obj['ymax'] > origin_im_size[0] or obj['xmin'] < 0 or obj['ymin'] < 0:
                continue
            color = (int(min(obj['class_id'] * 10, 255)),
                     min(obj['class_id'] * 2, 255), min(obj['class_id'] * 2, 255))
            det_label = labels_map[obj['class_id']] if labels_map and len(labels_map) >= obj['class_id'] else \
                str(obj['class_id'])

            coords = corners2center(obj['xmin'],obj['xmax'],obj['ymin'],obj['ymax'])
            detection = {}
            detection["label"] = det_label
            detection["box"] = obj


  #          cv2.circle(frame, ( int(coords[0]), int(coords[1])), 5, (0,255,0), -1)
   #         print(d[int(coords[1])][int(coords[0])])
            
         #   detection["coordinates"] = corners2center(obj['xmin'],obj['xmax'],obj['ymin'],obj['ymax'])
           
       #     dist = d[(obj["ymin"])+5:(obj["ymax"])-5,(obj["xmin"])+5:(obj["xmax"])-5]
        #    dist = dist[np.nonzero(dist)]/1000

#            dist2 = np.int_(d[(obj["ymin"])+5:(obj["ymax"])-5,(obj["xmin"])+5:(obj["xmax"])-5].flatten()/200)
 #           dist2 = dist2[np.nonzero(dist2)]
  #          count = np.bincount(dist2)
   #         ii = np.nonzero(count)[0]
    #        freq = np.vstack((ii,count[ii])).T
            
     #       count = 0
      #      prevfreq = 0
       #     estdist = 0
        #    for i in freq:
         #       if i[1] > prevfreq:
          #          prevfreq = i[1]
           #         estdist = i[0]/5
            #        count = 0
             #   else:
              #      count = count +1
               # if count > 20:
                #    break          

 #           if dist.size != 0:
  #              detection["depth"] = dist.min()
   #         else:
    #            detection["depth"] = -1

       #     detection["depth"] = estdist

            if detection["label"] == "Person":
                detection["equip"] = []
                detection["danger_score"] = 0
                detection["depth"] = d[int((obj["ymax"]+obj["ymin"])/2)][int((obj["xmax"] + obj["xmin"])/2)]/1000
                people.append(detection)
            else:
#                if detection["label"] == "Face":
 #                   detection["image"] = original_image[obj["ymin"]:obj["ymax"],obj["xmin"]:obj["xmax"]][...,::-1]
 #                   img = Image.fromarray(detection["image"])
  #                  img.save("example.png")
   #                 data = np.log(np.stack([d[(obj["ymin"]-10):(obj["ymax"]+10),(obj["xmin"]-10):(obj["xmax"]+10)]/1000 for i in range(3)], axis = 2) + 1)
    #                data = data / data.max()
     #               data = 255 * data
      #              depth = data.astype(np.uint8)
       #             depthimg = Image.fromarray(depth)
        #            depthimg.save("exampled.png")
                    
                others.append(detection)
                cv2.rectangle(frame, (obj['xmin'], obj['ymin']), (obj['xmax'], obj['ymax']), color, 2)
                cv2.putText(frame,
                        "#" + det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %' + ' ' ,
      (obj['xmin'], obj['ymin'] - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)
            
            #print(det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %' + ' ' + str(detection["depth"]) + " m")
        object_len = {"Handgun": 0.2, "Hat": 0.2, "Jacket": 0.8 ,"Knife" :0.1, "Rifle": 0.8, "Sunglasses": 0.05, "Police": 1.7 , "Face" :0.2}

        danger_weights = {"Handgun": 5, "Hat": 1, "Jacket": 1 ,"Knife" :3, "Person": 0 ,"Rifle": 5, "Sunglasses": 1, "Police": -6 , "Face" :0}

        for i in others:
            min_diff = 10000000000
            likely = -1
            for j in range(len(people)):
                if intersection_over_union(i["box"], people[j]["box"]) > 0:
                     if people[j]["depth"] != 0:
                         est_diff = (expected_len(i["box"], people[j]["depth"]) - object_len[i["label"]])**2
                         if min_diff > est_diff:
                             min_diff = est_diff
                             likely = j
             
            people[likely]["equip"].append(i)
            people[likely]["danger_score"] = people[likely]["danger_score"] + i["box"]["confidence"] * danger_weights[i["label"]]

        for i in people:
            if i["danger_score"] > 1:
                color = (0,0,255)
            elif i["danger_score"] > 0.2:
                color = (0,165,255)
            else:
                color = (0,255,0)
            obj = i["box"]
            cv2.rectangle(frame, (obj['xmin'], obj['ymin']), (obj['xmax'], obj['ymax']), color, 2)
            cv2.putText(frame,
                        "#" + i["label"] + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %' + ' ' + str(i["depth"]) + " m",
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
            break

    cv2.destroyAllWindows()


if __name__ == '__main__':
    sys.exit(main() or 0)
