# coding:utf-8

from socket import *
import threading, sys, json, re
from MyChat_Tools import Tools
from websocket import create_connection

HOST = '127.0.0.1'  ##
PORT = 8023
BUFSIZ = 8096  ##缓冲区大小  1K
ADDR = (HOST, PORT)

ws = create_connection("ws://127.0.0.1:8023")
userAccount = None


def register():
    myre = r"^[_a-zA-Z]\w{0,}"
    # 正则验证用户名是否合乎规范
    accout = input('Please input your account: ')
    # if not re.findall(myre, accout):
    #     print('Account illegal!')
    #     return None
    password1 = input('Please input your password: ')
    password2 = input('Please confirm your password: ')
    if not (password1 and password1 == password2):
        print('Password not illegal!')
        return None
    global userAccount
    userAccount = accout
    return (accout, password1)


class inputdata(threading.Thread):
    def run(self):
        try:
            while True:
                sendto = input('to>>:')
                msg = input('msg>>:')
                dataObj = {'to': sendto, 'msg': msg, 'from': userAccount}
                datastr = json.dumps(dataObj)
                ws.send(bytes(datastr, encoding="utf-8"))
        except:
            print("disconnected")


class getdata(threading.Thread):
    def run(self):
        try:
            while True:
                data = ws.recv()
                # print(data)
                dataObj = json.loads(data)
                # print(type(dataObj))
                if (type(dataObj) == dict):
                    print('\n{} -> {}'.format(dataObj['from'], dataObj['msg']))
        except:
            print("disconnected")


def main():
    try:
        while True:
            regInfo = register()
            if regInfo:
                datastr = json.dumps(regInfo)
                ws.send(bytes(datastr, encoding="utf-8"))
                break
        myinputd = inputdata()
        mygetdata = getdata()
        myinputd.start()
        mygetdata.start()
        myinputd.join()
        mygetdata.join()
    except:
        print("disconnected")


if __name__ == '__main__':
    main()
