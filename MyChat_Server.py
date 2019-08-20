# coding:utf-8
'''
file:MyChat_Server.py
date:2019/8/19
author:Mark
email:puhaozhou@163.com
platform:win10.x86_64 pycharm python3
desc:p2p communication serverside
'''
import socket
import threading
from MyChat_Tools import Tools
import json
import asyncio
import websockets

STATE = {"value": 0}
UserList = []  # 用户连接表，有几个用户连接，就会有几个websocket对象
HistoryMessage = []  #历史消息


##  连接列表，用来保存一个连接的信息（代号 地址和端口 连接对象）
class Connector(object):  # 连接对象类
    def __init__(self, account, password, conObj):
        self.account = account
        self.password = password
        self.conObj = conObj


def state_event():
    return json.dumps({"type": "state", **STATE})


async def register(data, websocket):
    print('registering')
    account = data[0]
    password = data[1]
    conObj = Connector(account, password, websocket)
    UserList.append(conObj)
    print(data)
    reply = {"from": "server", "msg": "registered"}
    reply = json.dumps(reply)
    await websocket.send(reply)


async def handler_accept(websocket, path):
    print("got connection from", websocket)
    reply = {"from": "server", "msg": "connected"}
    reply = json.dumps(reply)
    await websocket.send(reply)
    await handler_msg(websocket)


async def unregister(websocket):
    for user in UserList:
        if user.conObj == websocket:
            UserList.remove(user)


async def handler_msg(websocket):
    try:
        while True:
            data = await websocket.recv()
            dataobj = json.loads(data)
            if type(dataobj) == list:  # 是否是注册请求
                is_user_registered = filter(lambda x: x.account == dataobj[0], UserList)
                if not any(is_user_registered):  # 判断是否已经注册
                    await register(dataobj, websocket)
                    print(str(UserList).encode('utf-8'))
                else:  # 已存在该用户断开连接
                    reply = {"from": "server", "msg": "this account has been registered, please use another one!"}
                    reply = json.dumps(reply)
                    await websocket.send(reply)
                    break
            elif len(UserList) > 1 and type(dataobj) == dict:  # 注册用户大于1
                is_send_successful = False
                for user in UserList:
                    if dataobj['to'] == user.account:
                        datastr = json.dumps(dataobj)
                        print(datastr)
                        await user.conObj.send(datastr)
                        is_send_successful = True
                if not is_send_successful:
                    HistoryMessage.append(dataobj)
                    reply = {"from": "server", "msg": "sending message failed"}
                    reply = json.dumps(reply)
                    await websocket.send(reply)
            else:
                reply = {"from": "server", "msg": "nobody recevied!"}
                reply = json.dumps(reply)
                await websocket.send(reply)
    except:
        print("connection is closed")
    finally:
        await unregister(websocket)


if __name__ == '__main__':
    print('waiting for connection...')
    start_server = websockets.serve(handler_accept, "127.0.0.1", 8023)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
