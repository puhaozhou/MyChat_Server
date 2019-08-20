# coding:utf-8
'''
file:server.py
date:2017/9/10 12:43
author:lockey
email:lockey@123.com
platform:win7.x86_64 pycharm python3
desc:p2p communication serverside
'''
import socketserver, json
import subprocess

connLst = []  # 用户连接表，有几个用户连接，就会有几个websocket对象


##  连接列表，用来保存一个连接的信息（代号 地址和端口 连接对象）
class Connector(object):  # 连接对象类
    def __init__(self, account, password, addrPort, conObj):
        self.account = account
        self.password = password
        self.addrPort = addrPort
        self.conObj = conObj


class MyServer(socketserver.BaseRequestHandler):
    def handle(self):
        print("got connection from", self.client_address)
        registered = False  # 未注册
        while True:
            conn = self.request
            data = conn.recv(1024)
            if not data:
                continue
            dataobj = json.loads(data.decode('utf-8'))
            # 如果连接客户端发送过来的信息格式是一个列表且注册标识为False时进行用户注册
            if type(dataobj) == list and not registered:
                account = dataobj[0]
                password = dataobj[1]
                conObj = Connector(account, password, self.client_address, self.request)
                connLst.append(conObj)
                registered = True
                continue
            # 如果目标客户端在发送数据给目标客服端
            if len(connLst) > 1 and type(dataobj) == dict:  # 注册用户大于1
                sendok = False
                for obj in connLst:
                    if dataobj['to'] == obj.account:
                        obj.conObj.sendall(data)  # 向目标用户发送数据
                        sendok = True
                if sendok == False:
                    print('no target valid!')
            else:
                conn.sendall('nobody recevied!'.encode('utf-8'))
                continue


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(('127.0.0.1', 8022), MyServer)
    print('waiting for connection...')
    server.serve_forever()
