#coding:utf-8

from socket import *
import threading,sys,json,re
from MyChat_Tools import Tools
from websocket import create_connection

HOST = '127.0.0.1'  ##
PORT=8023
BUFSIZ = 8096  ##缓冲区大小  1K
ADDR = (HOST,PORT)

# tcpCliSock = socket(AF_INET,SOCK_STREAM)
# tcpCliSock.connect(ADDR)
ws = create_connection("ws://127.0.0.1:8023")
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
            datastr = json.dumps(dataObj)
            # msg = tools.generate_msg(bytes("recv: {}".format(datastr), encoding="utf-8"))
            # tcpCliSock.send(msg)
            #tools.send_msg(tcpCliSock, bytes("recv: {}".format(dataObj), encoding="utf-8"))
            ws.send(bytes(datastr, encoding="utf-8"))


class getdata(threading.Thread):
    def run(self):
        while True:
            data = ws.recv()
            #print(data)
            # dataObj = tools.get_data(data)
            print(data)
            dataObj = json.loads(data)
            print(type(dataObj))
            if(type(dataObj) == dict):
               print('\n{} -> {}'.format(dataObj['from'],dataObj['msg']))


def main():
    headers = tools.headers #获取包头
    #tcpCliSock.send(bytes(headers, encoding='utf-8')) #与服务端建立连接
    # ws.send(headers)
    # receive_data = ws.recv() #建立握手
    # if receive_data:
    #     print('success')
    while True:
        regInfo = register()
        if  regInfo:
            datastr = json.dumps(regInfo)
            # msg = tools.generate_msg(bytes("recv: {}".format(datastr), encoding="utf-8"))
            # tcpCliSock.send(msg)
            #tools.send_msg(tcpCliSock, bytes("recv: {}".format(regInfo), encoding="utf-8"))
            ws.send(bytes(datastr, encoding="utf-8"))
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