import struct
import socket
import hashlib
import base64
import logging
import time
import traceback

# 此功能用于与外界交互，可不使用
from threading import Thread

from utils.config import log_name

logger = logging.getLogger(log_name)


class WebSocketUtil(object):
    def __init__(self, port=8765, max_wait_user=5):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(max_wait_user)
        self.sock.setblocking(False)
        self.sock.settimeout(0)
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
        try:
            conn, addr = self.sock.accept()
        except BlockingIOError:
            time.sleep(0.3)
            return
        conn.settimeout(0)

        logger.info(f'websocket add new user: {len(self.users)} {conn} {self.users}')
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
        conn.sendall(bytes(response_str, encoding='utf-8'), )
        self.users.add(conn)

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
        if length < 126:
            token += struct.pack("B", length)
        elif length <= 0xFFFF:
            token += struct.pack("!BH", 126, length)
        else:
            token += struct.pack("!BQ", 127, length)
        msg = token + msg_bytes
        # 如果出错就是客户端断开连接
        try:
            conn.sendall(msg)
            logger.debug("websocket users end conn")
        except BlockingIOError:
            pass
        except:
            # 删除断开连接的记录
            error = str(traceback.format_exc())
            logger.warning(f'websocket users delete user: {self.users} {error}')
            self.users.remove(conn)
            conn.close()

    def wait_socket_connect(self):
        """
            循环等待客户端建立连接
        """
        while True:
            try:
                self.socket_connect()
            except:
                error = str(traceback.format_exc())
                logger.error(f"socket_connect error: {error}")

    def start_socket_server(self):
        """
            socket服务端监听客户端连接并批量推送数据
        """
        # 启线程循环等待客户端建立连接
        Thread(target=self.wait_socket_connect).start()
