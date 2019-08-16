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
import threading

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
    data = str(data, encoding="utf-8")
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


def generate_token(msg):
    key = msg + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    ser_key = hashlib.sha1(key.encode('utf-8')).digest()
    return base64.b64encode(ser_key)


def handler_accept(sock):
    while True:
        conn, addr = sock.accept()
        data = conn.recv(8096)
        print("got connection from", addr)
        headers = get_headers(data)
        # 对请求头中的sec-websocket-key进行加密
        response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
                       "Upgrade:websocket\r\n" \
                       "Connection: Upgrade\r\n" \
                       "Sec-WebSocket-Accept: %s\r\n" \
                       "WebSocket-Location: ws://%s\r\n\r\n"

        # magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        headers = get_headers(data)
        # 对请求头中的sec-websocket-key进行加密
        value = headers['Sec-WebSocket-Key']
        # ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())
        token = generate_token(value)
        print(token)
        print(headers['Host'])
        response_str = response_tpl % (token.decode('utf-8'), headers['Host'])
        conn.sendall(bytes(response_str, encoding='utf-8'))
        t = threading.Thread(target=handler_msg, args=(conn,addr))
        t.start()


def handler_msg(conn,addr):
    with conn as c:
        registered = False  # 未注册
        while True:
            data_recv = c.recv(8096)
            if data_recv[0:1] == b"\x81":
                data_parse = get_data(data_recv)
                print(data_parse)
            try:
                dataobj = json.loads(data_parse.decode('utf-8'))
            except IOError:
                print(str("data1 is null"))
                continue
            if type(dataobj) == list and not registered:
                account = dataobj[0]
                password = dataobj[1]
                conObj = Connector(account, password, addr, conn)
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
                        # send_msg(obj.conObj, bytes(data, encoding="utf-8"))
                        send_msg(obj.conObj, bytes("recv: {}".format(data_parse), encoding="utf-8"))
                        sendok = True
                if sendok == False:
                    print('no target valid!')
            else:
                # conn.sendall('nobody recevied!'.encode('utf-8'))
                send_msg(obj.conObj, bytes('nobody recevied!', encoding="utf-8"))
                continue
            # send_msg(c, bytes("recv: {}".format(data_parse), encoding="utf-8"))


def server_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 8023))
    sock.listen(5)
    t = threading.Thread(target=handler_accept(sock))
    t.start()


if __name__ == '__main__':
    print('waiting for connection...')
    server_socket()
