import socketio
import json 
from flask import Flask
from flask_socketio import SocketIO
import argparse
import sys
from threading import Thread
import pathlib
import datetime

def get_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir")
    return parser.parse_args(argv) 

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    print("Client Connected")    

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected.')


def start_server():
    socketio.run(app, debug = False)

def background_task(data_dir):
    data_files = pathlib.Path(data_dir).iterdir()
    data_files = sorted([x for x in data_files] , 
                        key = lambda x: datetime.datetime.fromisoformat(
                                     x.name.split(".")[0]
                                     ) 
                        )

    for _file in data_files:
        with open(_file) as f:
            try:
                data = json.loads(f.read())
                for _update in data:
                    if 'action' in _update:
                        socketio.emit('action', _update['action'])
                    if 'state' in _update:
                        socketio.emit('update', _update['state'])
            except:
                print("Error opening file")
                print(_file)






if __name__ == '__main__':
    import sys
    args = get_args(sys.argv[1:])
    data_dir = args.dir
    thread = Thread(target = start_server)
    thread.start()
    while(True):
        user_command  = input()
        if user_command == 'start':
            socketio.start_background_task(background_task, *(data_dir,) )
