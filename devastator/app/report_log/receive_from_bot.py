import json
import socket, pickle
from datetime import datetime
from collections import defaultdict
from devastator.app.Facerecognition.Call_Face_Rec import load_known, guess_who, frametest
from devastator.vision.gun_classifier import gun_classifier, GunClassifier

#ROBOT TO SEND report logs TO PORT 8888
HOST = "192.168.1.136"
# HOST = "192.168.1.185"
PORT = 8888
data = {}

def recv_obj(s):
    packets = []
    while True:
        packet = s.recv(1024)
        if not packet:
            break
        packets.append(packet)
    obj = pickle.loads(b"".join(packets))
    return obj

def update_data():
    idx = 1
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()

        try:
            while True:
                connection, _ = server.accept()
                data = recv_obj(connection)
                print(data)
                time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                curr_data = json.load(open('reports.json'))
                # print(curr_data)

                objects_of_interest = defaultdict(int)
                person_image = []
                gun_image = []
                # person_name = []
                # gun_model = []
                person_name = ""
                gun_name = ""
                for i in data:
                    # danger_score = i['danger_score']

                    for e in i['equip']:
                        if e['label'] == "Face":
                            person_image.append(e['image'])
                        elif e['label'] == "Rifle":
                            gun_image.append(e['image'])
                        objects_of_interest[e['label']] += 1

                for p in person_image:
                    person_who = guess_who(p, enc, names)
                    # person_name.append(person_who)
                    person_name += str(person_who) + " <p/>"

                for g in gun_image:
                    gun_what = gun_classifier.inference(g, path = False)
                    # gun_model.append(gun_what)
                    gun_name += str(gun_what) + " <p/>"

                objects_of_interest = ["{}: {}".format(label, count) for label, count in objects_of_interest.items()]
                objects_of_interest.append("Person: {}".format(len(data)))
                objects_of_interest = "<p/>".join(objects_of_interest)

                report_data = {
                    str(idx): {
                        "Time_Stamp": time_stamp,
                        "Threat_Direction": "HOW",
                        "Emotions_Present": "HOW",
                        "Gunshots": "HOW",
                        "Objects_Of_Interest": objects_of_interest,
                        "Persons_Detected": person_name,
                        "Guns_Model": gun_name
                    }
                }
                curr_data['data'].update(report_data)
                with open('reports.json', 'w') as outfile:
                    json.dump(curr_data, outfile,
                              indent=4)
                idx += 1


                # curr_data['data'].update(data)
                # with open('reports.json', 'w') as outfile:
                #     json.dump(curr_data, outfile,
                #               indent=4)

        finally:
            print("YAS")

if __name__ == '__main__':
    enc, names = load_known()
    GunClassifier(state_dict='resnet18_loss_1.056413.pt')
    update_data()