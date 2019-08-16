#coding:utf-8
'''
file:client.py.py
date:2017/9/10 11:01
author:lockey
email:lockey@123.com
platform:win7.x86_64 pycharm python3
desc:p2p communication clientside
'''
from socket import *
import threading,sys,json,re
from MyChat_Tools import Tools
from websocket import create_connection

ws = create_connection("ws://127.0.0.1:9002")
ws.send("Hello, World")##发送消息
result = ws.recv()##接收消息
ws.close()

HOST = '127.0.0.1'  ##
PORT=8023
BUFSIZ = 8096  ##缓冲区大小  1K
ADDR = (HOST,PORT)

tcpCliSock = socket(AF_INET,SOCK_STREAM)
tcpCliSock.connect(ADDR)
userAccount = None
def register():
    myre = r"^[_a-zA-Z]\w{0,}"
    #正则验证用户名是否合乎规范
    accout = input('Please input your account: ')
    # if not re.findall(myre, accout):
    #     print('Account illegal!')
    #     return None
    password1  = input('Please input your password: ')
    password2 = input('Please confirm your password: ')
    if not (password1 and password1 == password2):
        print('Password not illegal!')
        return None
    global userAccount
    userAccount = accout
    return (accout,password1)


class inputdata(threading.Thread):
    def run(self):
        while True:
            sendto = input('to>>:')
            msg = input('msg>>:')
            dataObj = {'to':sendto,'msg':msg,'from':userAccount}
            #datastr = json.dumps(dataObj)
            # msg = tools.generate_msg(bytes("recv: {}".format(datastr), encoding="utf-8"))
            # tcpCliSock.send(msg)
            tools.send_msg(tcpCliSock, bytes("recv: {}".format(dataObj), encoding="utf-8"))


class getdata(threading.Thread):
    def run(self):
        while True:
            data = tcpCliSock.recv(BUFSIZ)
            #print(data)
            dataObj = tools.get_data(data)
            if(type(dataObj) == dict):
               print('\n{} -> {}'.format(dataObj['froms'],dataObj['msg']))


def main():
    headers = tools.headers
    tcpCliSock.send(bytes(headers, encoding='utf-8'))
    receive_data = tcpCliSock.recv(BUFSIZ)
    if receive_data:
        print('success')
    while True:
        regInfo = register()
        if  regInfo:
            # datastr = json.dumps(regInfo)
            # msg = tools.generate_msg(bytes("recv: {}".format(datastr), encoding="utf-8"))
            # tcpCliSock.send(msg)
            tools.send_msg(tcpCliSock, bytes("recv: {}".format(regInfo), encoding="utf-8"))
            break
    myinputd = inputdata()
    mygetdata = getdata()
    myinputd.start()
    mygetdata.start()
    myinputd.join()
    mygetdata.join()


if __name__ == '__main__':
    tools = Tools()
    main()