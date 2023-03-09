import copy
import struct
import json
import socket
import hashlib
import base64

# 此功能用于与外界交互，可不使用
from threading import Thread

class WebSocketUtil(object):
    # global users
    # users = set()

    def __init__(self, port=8765, max_wait_user=5):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(max_wait_user)

        self.users = set()

    def get_headers(self, data):
        """将请求头转换为字典"""
        header_dict = {}

        data = str(data, encoding="utf-8")

        header, body = data.split("\r\n\r\n", 1)
        header_list = header.split("\r\n")
        for i in range(0, len(header_list)):
            if i == 0:
                if len(header_list[0].split(" ")) == 3:
                    header_dict['method'], header_dict['url'], header_dict['protocol'] = header_list[0].split(" ")
            else:
                k, v = header_list[i].split(":", 1)
                header_dict[k] = v.strip()
        return header_dict

    def socket_connect(self):
        """
            等待用户连接
        """
        conn, addr = self.sock.accept()
        self.users.add(conn)
        print('websocket add new user', conn, users)
        # 获取握手消息，magic string ,sha1加密  发送给客户端  握手消息
        data = conn.recv(8096)
        headers = self.get_headers(data)
        # 对请求头中的sec-websocket-key进行加密
        response_tpl = "HTTP/1.1 101 Switching Protocols\r\n" \
                       "Upgrade:websocket\r\n" \
                       "Connection: Upgrade\r\n" \
                       "Sec-WebSocket-Accept: %s\r\n" \
                       "WebSocket-Location: ws://%s%s\r\n\r\n"

        magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        value = headers['Sec-WebSocket-Key'] + magic_string
        ac = base64.b64encode(hashlib.sha1(value.encode('utf-8')).digest())
        response_str = response_tpl % (ac.decode('utf-8'), headers['Host'], headers['url'])

        # 响应握手信息
        conn.send(bytes(response_str, encoding='utf-8'), )

        # # 新的连接成功立马发一次数据
        data = {"message": "connect done"}
        self.send_msg(conn, bytes(json.dumps(data), encoding="utf-8"))

    # 向客户端发送数据
    def send_msg(self, conn, msg_bytes):
        """
            WebSocket服务端向客户端发送消息
        :param conn: 客户端连接到服务器端的socket对象,即： conn,address = socket.accept()
        :param msg_bytes: 向客户端发送的字节
        :return:
        """
        token = b"\x81"  # 接收的第一字节，一般都是x81不变
        length = len(msg_bytes)
        # print(length)
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)
        msg = token + msg_bytes
        # 如果出错就是客户端断开连接
        try:
            conn.send(msg)
        except Exception as e:
            # 删除断开连接的记录
            print('websocket delete user', self.users)
            self.users.remove(conn)

    def wait_socket_connect(self):
        """
            循环等待客户端建立连接
        """
        while True:
            self.socket_connect()

    def start_socket_server(self):
        """
            socket服务端监听客户端连接并批量推送数据
        """
        # 启线程循环等待客户端建立连接
        Thread(target=self.wait_socket_connect).start()
        # # 消息推送
        # while True:
        #     # 判断是否有客户端连接，有才推送消息
        #     if len(users):
        #         send_users = copy.copy(users)
        #         # 自定义的消息内容
        #         data = summary()
        #         # 遍历
        #         for user in send_users:
        #             self.send_msg(user, bytes(json.dumps(data), encoding="utf-8"))
