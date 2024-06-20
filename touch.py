import json
import sys
import threading
import time
import socket
import win32api
import win32con

import serial


class Touch:
    def __init__(self, port="COM33", baudrate=9600, touch_side="L", force_touch=False):
        self.touch_region_maps = {'A1': [1, 0, 0, 0], 'A2': [2, 0, 0, 0], 'A3': [4, 0, 0, 0], 'A4': [8, 0, 0, 0],
                                  'A5': [0, 1, 0, 0], 'A6': [0, 2, 0, 0], 'A7': [0, 4, 0, 0], 'A8': [0, 8, 0, 0],
                                  'E7': [0, 16, 0, 0], 'E8': [0, 32, 0, 0], 'B1': [0, 0, 1, 0], 'B2': [0, 0, 2, 0],
                                  'B3': [0, 0, 4, 0], 'B4': [0, 0, 8, 0], 'D7': [0, 0, 16, 0], 'D8': [0, 0, 32, 0],
                                  'E1': [0, 0, 64, 0], 'E2': [0, 0, 128, 0], 'E3': [0, 0, 256, 0], 'E4': [0, 0, 512, 0],
                                  'E5': [0, 0, 1024, 0], 'E6': [0, 0, 2048, 0], 'B5': [0, 0, 0, 1], 'B6': [0, 0, 0, 2],
                                  'B7': [0, 0, 0, 4], 'B8': [0, 0, 0, 8], 'C1': [0, 0, 0, 16], 'C2': [0, 0, 0, 32],
                                  'D1': [0, 0, 0, 64], 'D2': [0, 0, 0, 128], 'D3': [0, 0, 0, 256], 'D4': [0, 0, 0, 512],
                                  'D5': [0, 0, 0, 1024], 'D6': [0, 0, 0, 2048]}

        self.key_maps = {
            "L": {
                'K1': ord("W"), 'K2': ord("E"), 'K3': ord("D"), 'K4': ord("C"), 'K5': ord("X"), 'K6': ord("Z"), 'K7': ord("A"), 'K8': ord("Q"), "SEL": ord('3')
            },
            "R": {
                'K1': ord("B"), 'K2': ord("A"), 'K3': ord("S"), 'K4': ord("V"), 'K5': ord("N"), 'K6': ord("M"), 'K7': ord("J"), 'K8': ord("H"), "SEL": ord('2')
            }
        }
        self.force_touch = force_touch

        self._touch = serial.Serial(port, baudrate, timeout=1)

        self.allow_to_send_touch = False
        self._touch_side = touch_side

        if self._touch is None:
            return

        threading.Thread(target=self.__handle_remote_message).start()

    @staticmethod
    def __make_touch_send_pkg(mpr_touched_data):

        touch_map = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3),
                     (3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11),
                     (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (1, 4), (1, 5), (1, 6), (1, 7),
                     (1, 8), (1, 9), (1, 10), (1, 11), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11)]

        touch_data = 0

        for i in range(33, -1, -1):
            touch_data <<= 1
            mpr_id, port_id = touch_map[i]
            touch_data = (touch_data | ((mpr_touched_data[mpr_id] >> port_id) & 1))

        # 构造触摸数据包字符串
        touch_packet = bytearray()
        touch_packet.append(40)
        for _ in range(1, 8):
            byte = touch_data & 0b11111
            touch_packet.append(byte)
            touch_data >>= 5
        touch_packet.append(41)

        return touch_packet

    def send_touch(self, region: str):
        if self.allow_to_send_touch or self.force_touch:
            self.__write(self.__make_touch_send_pkg(self.touch_region_maps[region.upper()]))

    def send_multi_touch(self, regions: list[str]):
        if self.allow_to_send_touch or self.force_touch:
            pkg = [0, 0, 0, 0]
            for region in regions:
                if region.upper() in self.touch_region_maps:
                    current_region = self.touch_region_maps[region.upper()]
                    for i in range(len(current_region)):
                        pkg[i] += current_region[i]

            self.__write(self.__make_touch_send_pkg(pkg))

    def press_key(self, key: str):
        if (self.allow_to_send_touch or self.force_touch) and key in self.key_maps[self._touch_side].keys():
            win32api.keybd_event(self.key_maps[self._touch_side][key], 0, 0, 0)
            win32api.keybd_event(self.key_maps[self._touch_side][key], 0, win32con.KEYEVENTF_KEYUP, 0)


    @staticmethod
    def __get_hex_char(_hex):
        return chr(_hex)

    def __handle_remote_message(self):
        while True:
            try:
                if self._touch.in_waiting > 0:
                    recv = self._touch.read(6)[1: -1]
                    print(recv)
                    print(chr(recv[2]))
                    match chr(recv[2]):
                        case 'r':
                            print("sensor ratio")
                            self.__write(bytearray(b"(" + recv + b")"))
                        case 'k':
                            print("sensor sens")
                            self.__write(bytearray(b"(" + recv + b"}"))
                        case 'A':
                            print("allow send touch")
                            self.allow_to_send_touch = True
                        case 'E':
                            print("reset")
                            self.allow_to_send_touch = False
                        case 'L':
                            print("setting")
                        case _:
                            print("unknown")
                time.sleep(0.1)
            except KeyboardInterrupt:
                sys.exit()
            except Exception as e:
                print("Exception occurred: ", e)

    def __write(self, msg: str | bytearray):

        print(f"Send: {msg}")
        print()
        if isinstance(msg, bytearray):
            self._touch.write(msg)
            self._touch.flush()

        else:
            self._touch.write(msg.encode())
            self._touch.flush()


class TouchSocket:
    def __init__(self, port: int = 11414) -> None:
        self.PORT = port
        self._touch = Touch()
        self._server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self._server.bind(("0.0.0.0", self.PORT))
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.listen(128)
        print("Server listening on port", self.PORT)
        threading.Thread(target=self.__socket_main, daemon=True).start()

    def __handle_socket_connection(self, client: socket.socket):
        try:
            client.send(json.dumps({'msg': 'hi'}).encode("utf8"))
            while True:
                try:
                    recv_data = json.loads(client.recv(1024).decode("utf-8"))
                except json.decoder.JSONDecodeError:
                    client.send(json.dumps({'msg': 'err'}).encode("utf8"))
                    continue
                # {"action": "touch", "regions": ["A1", "B1", "E3"]}
                # {"action": "ping"}
                # {"action": "exit"}
                print(recv_data)
                match recv_data['action']:
                    case "touch":
                        if self._touch.allow_to_send_touch:
                            self._touch.send_multi_touch(list(map(lambda x: x.upper(), recv_data['regions'])))
                            client.send(json.dumps({'msg': 'ok'}).encode("utf8"))
                        else:
                            client.send(json.dumps({'msg': "unavailable"}).encode("utf8"))
                    case "ping":
                        client.send(json.dumps({'msg': 'pong'}).encode("utf8"))
                    case "exit":
                        client.send(json.dumps({'msg': 'bye'}).encode("utf8"))
                        client.close()
                        break
                    case _:
                        client.send(json.dumps({'msg': 'unknown'}).encode("utf8"))
        except ConnectionResetError as e:
            print("Connection closed")
            client.close()

    def __socket_main(self):
        while True:
            client_socket, address = self._server.accept()
            threading.Thread(target=self.__handle_socket_connection, args=(client_socket,)).start()


if __name__ == "__main__":
    # TouchSocket()
    t = Touch(force_touch=True)
    input("Press Enter")
    while True:
        time.sleep(60/(88*2))
        t.send_multi_touch(regions=list(t.touch_region_maps.keys()))