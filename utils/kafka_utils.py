import copy
import datetime
import json
import logging
import multiprocessing
import os.path
import time
import traceback

from kafka import KafkaProducer, KafkaConsumer
from multiprocessing import Process
from multiprocessing import Queue

# ConsumerRecord.value
from utils.config import max_size, WEB_PORT, p, LOG_FILE_DIR, log_name
from utils.log import setup_log
from utils.scocket_model import WebSocketUtil


class Producer:
    def __init__(self, logger, host, port, topic):
        self.logger = logger
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=[f'{host}:{port}'], api_version=(0, 10),
                                      max_request_size=20 * 1024 * 1024)

    def send(self, value):  # key@value 采用同样的key可以保证消息的顺序
        # return
        self.producer.send(self.topic, key=json.dumps(self.topic).encode('utf-8'),
                           value=json.dumps(value).encode('utf-8')).add_callback(self.on_send_success).add_errback(
            self.on_send_error).get()

    # 定义一个发送成功的回调函数
    def on_send_success(self, record_metadata):
        pass

    # 定义一个发送失败的回调函数
    def on_send_error(self, excp):
        self.logger.warning(f"send error: {excp}")


class MyProcess:
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            cls._instance = super(MyProcess, cls).__new__(cls)
        return cls._instance

    def __init__(self, config):
        self.send_queue = Queue(maxsize=200)
        self.websocket_queue = Queue(maxsize=200)
        self.origin_data = multiprocessing.Manager().dict()
        self.origin_data['data'] = {}
        self.origin_data['timestamp'] = time.time()

        # 子进程创建时，会将主进程的所有元素深拷贝一份，所以在子进程中，使用的是自己的生产者
        # 采用安全的队列，将队列传入进程中
        KAFKA_HOST, KAFKA_PORT, send_topic, take_topic = config.KAFKA_HOST, config.KAFKA_PORT, config.send_topic, config.take_topic
        p1 = Process(target=self.take, args=(KAFKA_HOST, KAFKA_PORT, take_topic, self.origin_data))
        p2 = Process(target=self.send, args=(self.send_queue, KAFKA_HOST, KAFKA_PORT, send_topic))
        p3 = Process(target=self.websocket_process, args=(self.websocket_queue,))
        p1.start()
        p2.start()
        p3.start()

    def websocket_process(self, websocket_queue):
        logger = setup_log(os.path.join(LOG_FILE_DIR, 'ws'), log_name, when="W0")
        # 子进程有一个websocket，用来与前端进行通信
        web = WebSocketUtil(port=WEB_PORT)
        web.start_socket_server()
        users = web.users
        while True:
            data = websocket_queue.get()
            logger.info(f"websocket users: {len(users)}, data size {len(data[0]['objs'])}")
            if len(users):
                # TODO 删除无关字段
                for obj in data[0]["objs"]:
                    lon, lat = p(obj['x'], -obj['y'], inverse=True)
                    obj.update(longitude=lon, latitude=lat)

                new_objs = []
                for obj in data[0]["objs"]:
                    new_objs.append(
                        {
                            'angleGps': obj['angleGps'],
                            'height': obj['height'],
                            'longitude': obj['longitude'],
                            'latitude': obj['latitude'],
                            'id': obj.get('id'),
                            'vehColor': obj.get('vehColor'),
                            'vehPlateColor': obj.get('vehPlateColor'),
                            'vehPlateString': obj.get('vehPlateString'),
                            'vehType': obj.get('vehType'),
                        }
                    )
                data[0]['objs'] = new_objs
                send_users = copy.copy(users)
                for user in send_users:
                    web.send_msg(user, bytes(json.dumps(data), encoding="utf-8"))

    # 用来向kafka发送消息
    def send(self, send_queue, *args):
        logger = setup_log(os.path.join(LOG_FILE_DIR, 'send'), log_name, when="W0")
        while True:
            try:
                producer = Producer(logger, *args)
                while True:
                    # 不断获取仿真轨迹发送至kafka
                    data = send_queue.get()
                    if len(data[0]["objs"]) > max_size:
                        logger.error(f'kafka send size too longer {len(data[0]["objs"])}')
                        return  # kill 进程，触发重启

                    for obj in data[0]["objs"]:
                        lon, lat = p(obj['x'], -obj['y'], inverse=True)
                        # obj.update(longitude=int(lon * 10000000), latitude=int(lat * 10000000), height=height_funs[obj['lane_number']](lon).tolist())
                        obj.update(longitude=int(lon * 10000000), latitude=int(lat * 10000000))
                    producer.send(data)
            except:
                error = str(traceback.format_exc())
                logger.error(f"kafka send error: {json.dumps(error)}")

    # 用来读取kafka的雷达轨迹消息
    def take(self, host, port, topic, origin_data):
        logger = setup_log(os.path.join(LOG_FILE_DIR, 'take'), log_name, when="W0")
        while True:
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=[f'{host}:{port}'],
                    auto_offset_reset='latest',  # 从头消费 新的 group_id & earliest & latest
                    # value_deserializer=json.loads,
                )

                for message in consumer:
                    message = json.loads(message.value)
                    position_id = message.get('positionId')

                    data = {}
                    for obj in message.get('objs', []):
                        if obj.get("longitude") and obj.get("latitude") and (
                                obj.get("vehPlateString") not in ['', 'unknown', None]):
                            x, y = p(obj['longitude'] / 10000000, obj['latitude'] / 10000000)

                            obj.update(
                                {
                                    "x": x,
                                    "y": -y,
                                    'plat': obj['vehPlateString'],
                                    'origin_angle': obj.get('angleGps') and obj.get('angleGps') / 10,
                                    'origin_speed': obj.get('speed', 2000) / 100,
                                    'car_type': obj.get('vehType'),
                                    'lane_id': obj.get('laneId') or 1,
                                    'position_id': position_id,
                                }
                            )

                            # TODO 对于超限车随机赋长宽高
                            # if random.randint(0, 100) == 0:
                            #     if obj.get('vehType') == 5:
                            #         obj.update(objLength=1850, objWidth=275, objHeight=412)
                            #     elif obj.get('vehType') == 9:
                            #         obj.update(objLength=1830, objWidth=281, objHeight=419)
                            data[obj.get("vehPlateString")] = obj

                    # 尽可能保证不加锁的状态下 数据不会重复取出
                    temp_data = origin_data['data']
                    temp_data.update(data)
                    if len(temp_data) < max_size:  # 防止数据量过大
                        origin_data['data'] = temp_data
            except:
                error = str(traceback.format_exc())
                logger.error(f"kafka take error: {json.dumps(error)}")
