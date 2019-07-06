###working prototype 2###
from flask import Flask, render_template, jsonify

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('jsontotabletest.html')


###copy this into logs.json
#make it such that the links are clickable?

@app.route('/index_get_data')

def loadLogs():
    with open('./logs2.json', 'r') as jsonf:
        data = json.load(jsonf)
    print(data)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)