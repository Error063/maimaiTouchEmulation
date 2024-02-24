import json

from flask import Flask, render_template, request, redirect
import touch as t
import socket

app = Flask(__name__, template_folder='templates')
t.TouchSocket()

print("Don't mind any error from serial ")
sock = socket.socket()
sock.connect(('localhost', 11414))
print(sock.recv(1024).decode('utf-8'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/touch')
def touch():
    region = request.args.get('region')
    sock.send(json.dumps({'action': "touch", "regions": [region]}).encode('utf-8'))
    return {'resp': 'ok', "data": json.loads(sock.recv(1024).decode('utf-8'))}


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9000, debug=True)
