# coding:utf-8
'''
file:server.py
date:2017/9/10 12:43
author:lockey
email:lockey@123.com
platform:win7.x86_64 pycharm python3
desc:p2p communication serverside
'''
import socket
import threading
from MyChat_Tools import Tools

connLst = []  # 用户连接表，有几个用户连接，就会有几个websocket对象


##  连接列表，用来保存一个连接的信息（代号 地址和端口 连接对象）
class Connector(object):  # 连接对象类
    def __init__(self, account, password, addrPort, conObj):
        self.account = account
        self.password = password
        self.addrPort = addrPort
        self.conObj = conObj


def handler_accept(sock):
    while True:
        conn, addr = sock.accept()
        data = conn.recv(8096) #接收握手请求
        print("got connection from", addr)
        # 对请求头中的sec-websocket-key进行加密
        response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
                       "Upgrade:websocket\r\n" \
                       "Connection: Upgrade\r\n" \
                       "Sec-WebSocket-Accept: %s\r\n" \
                       "WebSocket-Location: ws://%s\r\n\r\n"
        # print(data)
        headers = tools.get_headers(data)
        # 对请求头中的sec-websocket-key进行加密
        # print(headers)
        value = headers['Sec-WebSocket-Key']
        token = tools.generate_token(value)
        # print(token)
        # print(headers['Host'])
        response_str = response_tpl % (token.decode('utf-8'), headers['Host'])
        conn.sendall(bytes(response_str, encoding='utf-8'))  #建立握手
        t = threading.Thread(target=handler_msg, args=(conn,addr)) #开始通信
        t.start()


def handler_msg(conn,addr):
    with conn as c:
        registered = False  # 未注册
        while True:
            data_recv = c.recv(8096)
            print(data_recv)
            if data_recv[0:1] == b"\x81":
                data_parse = tools.get_data(data_recv)
                print(data_parse)
            # try:
            #     dataobj = json.loads(data_parse.decode('utf-8'))
            # except IOError:
            #     print(str("data1 is null"))
            #     continue
            if type(data_parse) == list and not registered:
                account = data_parse[0]
                password = data_parse[1]
                conObj = Connector(account, password, addr, conn)
                connLst.append(conObj)
                registered = True
                continue
            # print(str(connLst).encode('utf-8'))
            # 如果目标客户端在发送数据给目标客服端
            if len(connLst) > 1 and type(data_parse) == dict:  # 注册用户大于1
                sendok = False
                for obj in connLst:
                    if data_parse['to'] == obj.account:
                        # obj.conObj.sendall(data)  # 向目标用户发送数据
                        # send_msg(obj.conObj, bytes(data, encoding="utf-8"))
                        tools.send_msg(obj.conObj, bytes("recv: {}".format(data_parse), encoding="utf-8"))
                        sendok = True
                if not sendok:
                    print('no target valid!')
            else:
                # conn.sendall('nobody recevied!'.encode('utf-8'))
                tools.send_msg(conn, bytes('nobody recevied!', encoding="utf-8"))
                continue


def server_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 8023))
    sock.listen(5)
    t = threading.Thread(target=handler_accept(sock))
    t.start()


if __name__ == '__main__':
    print('waiting for connection...')
    tools = Tools()
    server_socket()
