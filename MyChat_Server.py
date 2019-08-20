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
UserList = []  # an array used to store user object
Suspended_Message = []  # an array used to store messages that need to be suspended


# a class of connected users, which consists of user's account, password and connection
class Connector(object):
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
    try:
        await websocket.send(reply)
        result = True
    except:
        result = False
    return result


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


async def send_suspended_msg(websocket, current_user):
    for msg in Suspended_Message:
        if msg["to"] == current_user:
            suspended_msgstr = json.dumps(msg)
            await websocket.send(suspended_msgstr)
            Suspended_Message.remove(msg)


async def handler_msg(websocket):
    try:
        while True:
            data = await websocket.recv()
            dataobj = json.loads(data)
            # check whether this message is a register request message
            if type(dataobj) == list:
                is_user_registered = filter(lambda x: x.account == dataobj[0], UserList)
                # check whether current user has registered, if not, then register
                if not any(is_user_registered):
                    is_register_successful = await register(dataobj, websocket)
                    # print(str(UserList).encode('utf-8'))
                    has_suspended_msg = filter(lambda x: x["to"] == dataobj[0], Suspended_Message)
                    # check whether this newly-registered user has suspended messages
                    if is_register_successful and any(has_suspended_msg):
                        await send_suspended_msg(websocket, dataobj[0])
                # if the user already exists
                else:
                    reply = {"from": "server", "msg": "this account has been registered, please use another one!"}
                    reply = json.dumps(reply)
                    await websocket.send(reply)
                    break
            # if there exists at least one user who is online, and the type of the message is a normal chat
            # message
            elif len(UserList) >= 1 and type(dataobj) == dict:
                is_send_successful = False
                for user in UserList:
                    if dataobj['to'] == user.account:
                        new_msgstr = json.dumps(dataobj)
                        print(new_msgstr)
                        await user.conObj.send(new_msgstr)
                        is_send_successful = True
                # if the target user does not exist, then store this message in
                # suspended_message
                if not is_send_successful:
                    Suspended_Message.append(dataobj)
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
