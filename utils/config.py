import os

from pyproj import Proj

car_veh_type_code_mapping = {
    1: 13, #轿车
    2: 14, #SUV
    3: 15, #小客面包车
    4: 16, #中客、轻客
    5: 17, #大客、公交
    6: 18, #小型货车
    7: 19, #轻型货车
    8: 25, #中型货车
    9: 20, #重型货车
    10: 21, #MPV
    11: 26, #皮卡
    12: 22, #厢式货车
    13: 23, #摩托车
    14: 24, #其他
}

car_veh_type_name_mapping = {
    1:  "轿车",
    2:  "SUV",
    3:  "小客车",
    4:  "中客、轻客",
    5:  "大客、公交",
    6:  "小型货车",
    7:  "轻型货车",
    8:  "中型货车",
    9:  "重型货车",
    10: "MPV",
    11: "皮卡",
    12: "厢式货车",
    13: "摩托车",
    14: "其他",
}

# 缓冲区长度
buffer_length = 100

# 邻居车牌距离
neighbor_distance = 100

# 平滑处理允许的时间
smoothing_time = 3000  # ms

# kafka 配置
KAFKA_HOST = '192.168.10.91'
KAFKA_PORT = 9092
send_topic = "MECFUSION"
take_topic = "HolographicRealTimeTarget"

# 仿真精度
accuracy = 3

accemultiples=1

# 数据量上限
max_size = 3000

# 项目目录
BASEPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 路网文件位置
TESSNG_FILE_PATH = os.path.join(BASEPATH, 'Data', "bh.tess")

WEB_PORT = 8009

p = Proj('+proj=tmerc +lon_0=121.43806548017288 +lat_0=31.243770912743578 +ellps=WGS84')
