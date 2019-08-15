# coding:utf-8
'''
file:server.py
date:2017/9/10 12:43
author:lockey
email:lockey@123.com
platform:win7.x86_64 pycharm python3
desc:p2p communication serverside
'''
import base64
import hashlib
import socket
import socketserver, json
import subprocess
import struct

connLst = []  # 用户连接表，有几个用户连接，就会有几个websocket对象


##  连接列表，用来保存一个连接的信息（代号 地址和端口 连接对象）
class Connector(object):  # 连接对象类
    def __init__(self, account, password, addrPort, conObj):
        self.account = account
        self.password = password
        self.addrPort = addrPort
        self.conObj = conObj


def get_headers(data):
    headers = {}
    data = str(data,encoding="utf-8")
    print(data)
    header, body = data.split("\r\n\r\n", 1)
    header_list = header.split("\r\n")
    for i in header_list:
        i_list = i.split(":", 1)
        if len(i_list) >= 2:
            headers[i_list[0]] = "".join(i_list[1::]).strip()
        else:
            i_list = i.split(" ", 1)
            if i_list and len(i_list) == 2:
                headers["method"] = i_list[0]
                headers["protocol"] = i_list[1]
    return headers


def get_data(info):
    payload_len = info[1] & 127
    if payload_len == 126:
        extend_payload_len = info[2:4]
        mask = info[4:8]
        decoded = info[8:]
    elif payload_len == 127:
        extend_payload_len = info[2:10]
        mask = info[10:14]
        decoded = info[14:]
    else:
        extend_payload_len = None
        mask = info[2:6]
        decoded = info[6:]

    bytes_list = bytearray()  # 这里我们使用字节将数据全部收集，再去字符串编码，这样不会导致中文乱码
    for i in range(len(decoded)):
        chunk = decoded[i] ^ mask[i % 4]  # 解码方式
        bytes_list.append(chunk)
    print(bytes_list)
    body = str(bytes_list, encoding='utf-8')
    return body


def send_msg(conn, msg_bytes):
    token = b"\x81"
    length = len(msg_bytes)
    if length < 126:
        token += struct.pack("B", length)
    elif length <= 0xFFFF:
        token += struct.pack("!BH", 126, length)
    else:
        token += struct.pack("!BQ", 127, length)

    msg = token + msg_bytes
    conn.sendall(msg)
    return True


class MyServer(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request
        print("got connection from", self.client_address)
        data = conn.recv(8096)
        data = get_data(data)
        print(data)
        response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
                       "Upgrade:websocket\r\n" \
                       "Connection: Upgrade\r\n" \
                       "Sec-WebSocket-Accept: %s\r\n" \
                       "WebSocket-Location: ws://%s%s\r\n\r\n"

        magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        headers = get_headers(data)
        # 对请求头中的sec-websocket-key进行加密
        value = headers['Sec-WebSocket-Key'] + magic_string
        ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())
        response_str = response_tpl % (ac.decode('utf-8'), headers['Host'], headers['url'])
        conn.sendall(bytes(response_str, encoding='utf-8'))

        registered = False  # 未注册
        while True:
            conn = self.request
            data = conn.recv(8096)
            data = get_data(data)
            print(data)
            print(registered)
            try:
                dataobj = json.loads(data.decode('utf-8'))
            except IOError:
                print("data is null")
                continue
            # 如果连接客户端发送过来的信息格式是一个列表且注册标识为False时进行用户注册
            if type(dataobj) == list and not registered:
                account = dataobj[0]
                password = dataobj[1]
                conObj = Connector(account, password, self.client_address, self.request)
                connLst.append(conObj)
                register = True
                continue
            # print(str(connLst).encode('utf-8'))
            # 如果目标客户端在发送数据给目标客服端
            if len(connLst) > 1 and type(dataobj) == dict:  # 注册用户大于1
                sendok = False
                for obj in connLst:
                    if dataobj['to'] == obj.account:
                        # obj.conObj.sendall(data)  # 向目标用户发送数据
                        send_msg(obj.conObj, bytes(data, encoding="utf-8"))
                        sendok = True
                if sendok == False:
                    print('no target valid!')
            else:
                # conn.sendall('nobody recevied!'.encode('utf-8'))
                send_msg(obj.conObj, bytes('nobody recevied!', encoding="utf-8"))
                continue


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('127.0.0.1', 8023), MyServer)
    print('waiting for connection...')
    server.serve_forever()
