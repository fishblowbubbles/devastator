###is the server in this case

import json
from flask_cors import CORS
import socket, pickle

#########################################################
###Final Working Prototype###
#NOTE:
'''
Run receive_frm_bot.py concurrently with robot_server.py and open the html file
receive_frm_bot receives the data from Wende and converts it into a json file for robot_server.py to use
For demo, ensure reports.json consist of only index 0 data => which is example
'''
from flask import Flask, render_template, jsonify

app = Flask(__name__)
CORS(app)



HOST = "192.168.1.136"
PORT = 8888


@app.route('/')
def index():
    return render_template('jsontotabletest.html')

@app.route('/index_get_data')
def loadLogs():
    curr_data = json.load(open('reports.json'))
    print(curr_data)
    return jsonify(curr_data)

    # with open('./logs2.json', 'r') as jsonf:
    #     data = json.load(jsonf)
    # print(data)
    # return jsonify(data)

if __name__ == '__main__':
    # x = Thread(target=update_data(), args=(1,))
    # app = Thread(target=app.run(debug=True,host = '127.0.0.1',port=5000),args=(1,))
    # x.start()
    # app.start()
    app.run(debug=True,host = '127.0.0.1',port=5000)