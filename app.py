import datetime
import json
import time

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import touch as t

app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app, cors_allowed_origins="*")  # 允许跨域请求
touch = t.Touch(port="COM33", baudrate=9600, touch_side="L", force_touch=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/disable-gesture')
def disable_gesture():
    return render_template('index.html')


# @app.route('/touch')
# def touch_handler():
#     region = request.args.get('region')
#     # sock.send(json.dumps({'action': "touch", "regions": [region]}).encode('utf-8'))
#     print(type(touch))
#     touch.send_multi_touch([region])
#     return {'resp': 'ok', "data": ""}


@socketio.on('ping')
def handle_ping(data):
    emit('pong', 'pong')


@socketio.on('message')
def handle_message(data):
    print(data)
    try:
        data = json.loads(data)
    except Exception as e:
        emit('response', json.dumps({'msg': 'json parse err', 'action': 'err'}))
        return None
    print(data)
    match data["action"]:
        case 'touch':
            if touch.allow_to_send_touch:
                touch.send_multi_touch(data["regions"])
                emit('response', json.dumps({'msg': 'ok', "action": 'touch'}))
            else:
                emit('response', json.dumps({'msg': 'not allowed', 'action': 'touch'}))
        case 'press':
            if touch.allow_to_send_touch or True:
                if data["key"] in touch.key_maps[touch._touch_side]:
                    touch.press_key(data["key"])
                    emit('response', json.dumps({'msg': 'ok', "action": 'press'}))
                else:
                    emit('response', json.dumps({'msg': 'unknown key', 'action': 'press'}))
                emit('response', json.dumps({'msg': 'ok', "action": 'press'}))
            else:
                emit('response', json.dumps({'msg': 'not allowed', 'action': 'press'}))
        case 'ping':
            emit('response', json.dumps({'msg': 'pong', "action": "ping"}))
        case 'check':
            emit('response', json.dumps({'msg': str(touch.allow_to_send_touch).lower(), 'action': 'check'}))
        case _:
            emit('response', json.dumps({'msg': 'unknown action', 'action': data['action']}))


if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=9000, debug=True)
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(('0.0.0.0', 8080), app, handler_class=WebSocketHandler)
    print('server start')
    server.serve_forever()