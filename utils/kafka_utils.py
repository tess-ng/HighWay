import copy
import datetime
import json
import multiprocessing
import os.path
import time
import traceback

from kafka import KafkaProducer, KafkaConsumer, TopicPartition
from multiprocessing import Process
from multiprocessing import Queue

# ConsumerRecord.value
from utils.config import max_size, p


class Producer:
    def __init__(self, host, port, topic):
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=[f'{host}:{port}'], api_version=(0, 10),
                                      max_request_size=20 * 1024 * 1024)

    def send(self, value):  # key@value 采用同样的key可以保证消息的顺序
        #return
        self.producer.send(self.topic, key=json.dumps(self.topic).encode('utf-8'),
                           value=json.dumps(value).encode('utf-8')).add_callback(self.on_send_success).add_errback(
            self.on_send_error).get()

    # 定义一个发送成功的回调函数
    def on_send_success(self, record_metadata):
        pass

    # 定义一个发送失败的回调函数
    def on_send_error(self, excp):
        print(f"send error: {excp}")


class MyProcess:
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            cls._instance = super(MyProcess, cls).__new__(cls)
        return cls._instance

    def __init__(self, config):
        # self.take_queue = Queue(maxsize=20)
        self.send_queue = Queue(maxsize=200)
        self.websocket_queue = Queue(maxsize=1000)
        self.origin_data = multiprocessing.Manager().dict()
        self.origin_data['data'] = {}
        self.origin_data['timestamp'] = time.time()

        # 子进程创建时，会将主进程的所有元素深拷贝一份，所以在子进程中，使用的是自己的生产者
        # 采用安全的队列，将队列传入进程中
        KAFKA_HOST, KAFKA_PORT, send_topic, take_topic = config.KAFKA_HOST, config.KAFKA_PORT, config.send_topic, config.take_topic
        p1 = Process(target=self.take, args=(KAFKA_HOST, KAFKA_PORT, take_topic, self.origin_data))
        p2 = Process(target=self.send, args=(self.send_queue, KAFKA_HOST, KAFKA_PORT, send_topic))
        p1.start()
        p2.start()

    # 用来向kafka发送消息
    def send(self, send_queue, *args):
        # return
        # producer 和 users 列表都在子进程初始化，不会影响主进程
        # height_funs = get_height_funs()
        while True:
            try:
                producer = Producer(*args)
                while True:
                    # 不断获取仿真轨迹发送至kafka
                    data = send_queue.get()
                    if len(data[0]["objs"]) > max_size:
                        print('kafka send size toor longer', len(data[0]["objs"]))
                        return  # kill 进程，触发重启
                    for obj in data[0]["objs"]:
                        lon, lat = p(obj['x'], -obj['y'], inverse=True)
                        # obj.update(longitude=lon * 10000000, latitude=lat * 10000000, height=height_funs[obj['lane_number']](lon).tolist())
                        obj.update(longitude=int(lon * 10000000), latitude=int(lat * 10000000))
                    producer.send(data)
            except:
                error = str(traceback.format_exc())
                print("kafka send error:", error)

    # 用来读取kafka的雷达轨迹消息
    def take(self, host, port, topic, origin_data):
        while True:
            try:
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=[f'{host}:{port}'],
                    auto_offset_reset='latest',  # 从头消费 新的 group_id & earliest & latest
                    #value_deserializer=json.loads,
                )

                for message in consumer:
                    message = json.loads(message.value)
                    data = {}
                    for obj in message.get('objs', []):
                        if obj.get("longitude") and obj.get("latitude") and (
                                obj.get("vehPlateString") not in ['', 'unknown', None]):
                            x, y = p(obj['longitude'] / 10000000, obj['latitude'] / 10000000)
                            obj.update(x=x, y=-y)
                            data[obj.get("vehPlateString")] = obj

                    # 尽可能保证不加锁的状态下 数据不会重复取出
                    temp_data = origin_data['data']
                    temp_data.update(data)
                    if len(temp_data) < max_size:  # 防止数据量过大
                        origin_data['data'] = temp_data
            except:
                error = str(traceback.format_exc())
                print("send error:", json.dumps(error))
