import argparse
import sys
from multiprocessing import Process

from robot.helpers import get_data
from robot.realsense import D435i
from robot.respeaker import ReSpeaker
from robot.romeo import Romeo
from robot.xpad import XPad
from sound.helpers import vokaturi_func

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", action="store_true")
    parser.add_argument("--app", action="store_true")
    args = parser.parse_args()

    if args.robot:
        # load the hardware
        devices = {"realsense": D435i(),
                   "respeaker": ReSpeaker(),
                   "romeo": Romeo()}
        # load your algorithms
    elif args.app:
        devices = {"xpad": XPad()}
    else:
        sys.exit()

    processes = {}

    for name, device in devices.items():
        processes[name] = Process(target=device.run)

    for name, device in processes.items():
        device.start()
        print("ready")

    """
    while True:
        frame = main()[0]
        detection = main()[1] #gives a list of dictionaries

        #### assume data structure of detection is:
        #### eg. detection = [{"depth":0.762,"danger_score":3.44,"equip":[{"label":"Rifle","box":{}}],"label":"Person","box":{}},{"depth":0.762,"danger_score":3.44,"equip":[{"label":"Rifle","box":{}},{"label":"Handgun","box":{}}],"label":"Person","box":{}}]
        StoreArgs.person_count = len(detection)

        for i in detection:
            for j in i["equip"]:
                if j["label"] == "Rifle":
                    StoreArgs.rifle_count += 1

                elif j["label"] == "Handgun":
                    StoreArgs.handgun_count += 1

                elif j["label"] == "Knife":
                    StoreArgs.knife_count += 1

                elif j["label"] == "Jacket":
                    StoreArgs.jacket_count += 1

                elif j["label"] == "Sunglasses":
                    StoreArgs.sunglass_count += 1

                elif j["label"] == "Police":
                    StoreArgs.police_count += 1

                elif j["label"] == "Hat":
                    StoreArgs.hat_count += 1

        ###format the data for objects of interest to parse into report ui app
        StoreArgs.obj_of_interest = "Handgun: " + str(StoreArgs.handgun_count) + "  <p/> " + "Jacket: " + str(StoreArgs.jacket_count) + " <p/> " + "Knife: " + str(StoreArgs.knife_count) + " <p/> " + "Person: " + str(StoreArgs.person_count) + " <p/> " + "Rifle " + str(rifle_count) + " <p/> " + "Sunglasses: " + str(StoreArgs.sunglass_count) + " <p/> " + "Police: " + str(StoreArgs.police_count) + " <p/> "
        JSON_INFO = {
            "data": {
                "logs1": {
                    "Time_Stamp": "12:10:17",
                    "Robot_Coordinates": "x,y,z",
                    "Threat_Direction": "x,y,z",
                    "Emotions_Present": "Fear",
                    "Gunshots": "Detected",
                    "Objects_Of_Interest": StoreArgs.obj_of_interest,
                    "More_Details": "<a href= www.google.com.sg>www.viewmorehere.com  </a>"
                }
            }
        }




        # #--------- get yolo frame ---------
        # input_stream = StoreArgs.input_stream
        # host = StoreArgs.host
        # port = StoreArgs.port
        #
        # frame = get_frame(input_stream, host, port) #host and port from call_yolo_display
        #
        # # ------------------------------------------- Loading model to the plugin -----------------------------------------
        # device = StoreArgs.device
        # labels = StoreArgs.labels
        # model_xml = StoreArgs.model_xml
        # model_bin = StoreArgs.model_bin
        # plugin_dir = StoreArgs.plugin_dir
        # cpu_extension = StoreArgs.cpu_extension
        #
        # net, exec_net = load_model(device, labels, model_xml, model_bin, plugin_dir, cpu_extension)
        #
        # #----------------------- yolo detection ------------------------
        # # mapping labels
        # labels_map = StoreArgs.labels_map
        # prob_thresh = StoreArgs.prob_thresh
        # iou_thresh = StoreArgs.iou_thresh
        # depth_given = StoreArgs.depth_given
        #
        # detection = detect(frame, net, exec_net, labels_map, prob_thresh, iou_thresh, depth_given) #gives a list of dictionaries?

        #------------------------ aruco
        # get_frame()
        # yolo_detect()
        # acoular_detect()
        # send_to_app()
