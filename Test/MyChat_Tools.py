# coding:utf-8

import base64
import hashlib
import random
import struct


class Tools:
    def __init__(self):
        self.init = 1

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def generate_msg(msg_bytes):
        token = b"\x81"
        length = len(msg_bytes)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)

        msg = token + msg_bytes
        return msg

    @staticmethod
    def generate_token(msg):
        key = msg + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        ser_key = hashlib.sha1(key.encode('utf-8')).digest()
        return base64.b64encode(ser_key)

    @property
    def headers(self):
        headers_base =  "GET / HTTP/1.1\r\n" \
                        "Host: 127.0.0.1:8023\r\n" \
                        "Connection: Upgrade\r\n" \
                        "Pragma: no-cache\r\n" \
                        "Cache-Control: no-cache\r\n" \
                        "User-Agent: Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Mobile Safari/537.36\r\n" \
                        "Upgrade: websocket\r\n" \
                        "Origin: http://localhost:8080\r\n" \
                        "Sec-WebSocket-Version: 13\r\n" \
                        "Accept-Encoding: gzip, deflate, br\r\n" \
                        "Accept-Language: zh-CN,zh;q=0.9\r\n" \
                        "Sec-WebSocket-Key: 6Q3E2AOc7eRZ5Hma0328qA==\r\n" \
                        "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits\r\n\r\n"
        return headers_base
