###is the server in this case

import json
from flask_cors import CORS
from threading import Thread

import socket, pickle

#########################################################
###working prototype 2###
from flask import Flask, render_template, jsonify
from receive_frm_bot import *

app = Flask(__name__)
CORS(app)


HOST = "192.168.1.136"
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
    global data
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()

        try:
            while True:
                connection, _ = server.accept()
                data = recv_obj(connection)
        finally:
            print("data updated")


@app.route('/')
def index():
    return render_template('jsontotabletest.html')


###copy this into logs.json
#make it such that the links are clickable?

@app.route('/index_get_data')

def loadLogs():
    print(data)
    return jsonify(data)

    # with open('./logs2.json', 'r') as jsonf:
    #     data = json.load(jsonf)
    # print(data)
    # return jsonify(data)

if __name__ == '__main__':
    x = Thread(target=update_data(), args=(1,))
    x.start()
    app.run(debug=True)