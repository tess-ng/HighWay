import collections
import json
import os
import logging

from pyproj import Proj

# 变道频率
change_lane_frequency = 0.1

# 雷达映射后可能行驶的路段
LD_create_link_mapping = {'CD003': {'is_create': False, 'links': []}, 'CD004': {'is_create': False, 'links': []}, 'CD005': {'is_create': False, 'links': []}, 'CD101': {'is_create': True, 'links': [28, 11]}, 'CD102': {'is_create': False, 'links': []}, 'CD103': {'is_create': True, 'links': [11]}, 'CD104': {'is_create': False, 'links': []}, 'CD105': {'is_create': True, 'links': [11]}, 'CD106': {'is_create': True, 'links': [11]}, 'CD107': {'is_create': False, 'links': []}, 'CD108': {'is_create': True, 'links': [11, 43]}, 'CD109': {'is_create': True, 'links': [15]}, 'CD110': {'is_create': False, 'links': []}, 'CD111': {'is_create': False, 'links': []}, 'CD112': {'is_create': True, 'links': [15]}, 'CD113': {'is_create': True, 'links': [15]}, 'CD114': {'is_create': True, 'links': [15]}, 'CD115': {'is_create': False, 'links': []}, 'CD116': {'is_create': False, 'links': []}, 'CD117': {'is_create': False, 'links': []}, 'CD118': {'is_create': False, 'links': []}, 'CD119': {'is_create': False, 'links': []}, 'CD120': {'is_create': False, 'links': []}, 'CD121': {'is_create': False, 'links': []}, 'CD122': {'is_create': False, 'links': []}, 'CD123': {'is_create': False, 'links': []}, 'CD124': {'is_create': False, 'links': []}, 'CD125': {'is_create': False, 'links': []}, 'CD126': {'is_create': False, 'links': []}, 'CD127': {'is_create': False, 'links': []}, 'CD128': {'is_create': False, 'links': []}, 'CD129': {'is_create': False, 'links': []}, 'CD130': {'is_create': False, 'links': []}, 'CD131': {'is_create': False, 'links': []}, 'CD132': {'is_create': False, 'links': []}, 'CD133': {'is_create': False, 'links': []}, 'CD134': {'is_create': False, 'links': []}, 'CD135': {'is_create': False, 'links': []}, 'CD136': {'is_create': False, 'links': []}, 'CD137': {'is_create': False, 'links': []}, 'CD138': {'is_create': False, 'links': []}, 'CD139': {'is_create': False, 'links': []}, 'CD140': {'is_create': False, 'links': []}, 'CD141': {'is_create': False, 'links': []}, 'CD142': {'is_create': False, 'links': []}, 'CD143': {'is_create': False, 'links': []}, 'CD144': {'is_create': False, 'links': []}, 'CD145': {'is_create': False, 'links': []}, 'CD146': {'is_create': False, 'links': []}, 'CD147': {'is_create': False, 'links': []}, 'CD148': {'is_create': False, 'links': []}, 'CD149': {'is_create': False, 'links': []}, 'CD150': {'is_create': False, 'links': []}, 'CD151': {'is_create': False, 'links': []}, 'CD152': {'is_create': False, 'links': []}, 'CD153': {'is_create': False, 'links': []}, 'CD154': {'is_create': False, 'links': []}, 'CD155': {'is_create': False, 'links': []}, 'CD156': {'is_create': False, 'links': []}, 'CD157': {'is_create': False, 'links': []}, 'CD158': {'is_create': False, 'links': []}, 'CD159': {'is_create': False, 'links': []}, 'CD160': {'is_create': False, 'links': []}, 'CD161': {'is_create': False, 'links': []}, 'CD162': {'is_create': False, 'links': []}, 'CD163': {'is_create': False, 'links': []}, 'CD201': {'is_create': False, 'links': []}, 'CD202': {'is_create': False, 'links': []}, 'CD203': {'is_create': False, 'links': []}, 'CD204': {'is_create': False, 'links': []}, 'CD205': {'is_create': False, 'links': []}, 'CD206': {'is_create': False, 'links': []}, 'CD207': {'is_create': False, 'links': []}, 'CD208': {'is_create': False, 'links': []}, 'CD209': {'is_create': False, 'links': []}, 'CD210': {'is_create': False, 'links': []}, 'CD211': {'is_create': False, 'links': []}, 'CD212': {'is_create': False, 'links': []}, 'CD213': {'is_create': False, 'links': []}, 'CD214': {'is_create': False, 'links': []}, 'CD215': {'is_create': False, 'links': []}, 'CD216': {'is_create': False, 'links': []}, 'CD217': {'is_create': False, 'links': []}, 'CD218': {'is_create': False, 'links': []}, 'CD219': {'is_create': False, 'links': []}, 'CD220': {'is_create': False, 'links': []}, 'CD221': {'is_create': False, 'links': []}, 'CD222': {'is_create': False, 'links': []}, 'CD223': {'is_create': False, 'links': []}, 'CD224': {'is_create': False, 'links': []}, 'CD225': {'is_create': False, 'links': []}, 'CD226': {'is_create': False, 'links': []}, 'CD227': {'is_create': False, 'links': []}, 'CD228': {'is_create': False, 'links': []}, 'CD229': {'is_create': False, 'links': []}, 'CD230': {'is_create': False, 'links': []}, 'CD231': {'is_create': False, 'links': []}, 'CD232': {'is_create': False, 'links': []}, 'CD233': {'is_create': False, 'links': []}, 'CD234': {'is_create': False, 'links': []}, 'CD235': {'is_create': False, 'links': []}, 'CD236': {'is_create': False, 'links': []}, 'CD237': {'is_create': False, 'links': []}, 'CD238': {'is_create': False, 'links': []}, 'CD239': {'is_create': False, 'links': []}, 'CD240': {'is_create': False, 'links': []}, 'CD241': {'is_create': False, 'links': []}, 'CD242': {'is_create': False, 'links': []}, 'CD243': {'is_create': False, 'links': []}, 'CD244': {'is_create': False, 'links': []}, 'CD245': {'is_create': False, 'links': []}, 'CD246': {'is_create': False, 'links': []}, 'CD247': {'is_create': False, 'links': []}, 'CD248': {'is_create': False, 'links': []}, 'CD249': {'is_create': False, 'links': []}, 'CD250': {'is_create': False, 'links': []}, 'CD251': {'is_create': False, 'links': []}, 'CD252': {'is_create': False, 'links': []}, 'CD253': {'is_create': False, 'links': []}, 'CD254': {'is_create': False, 'links': []}, 'CD255': {'is_create': False, 'links': []}, 'CD256': {'is_create': False, 'links': []}, 'CD257': {'is_create': False, 'links': []}, 'CD258': {'is_create': False, 'links': []}, 'CD259': {'is_create': False, 'links': []}, 'CD260': {'is_create': False, 'links': []}, 'CD261': {'is_create': False, 'links': []}, 'CD262': {'is_create': False, 'links': []}, 'CD263': {'is_create': False, 'links': []}, 'CD264': {'is_create': False, 'links': []}, 'CD265': {'is_create': False, 'links': []}, 'CD266': {'is_create': False, 'links': []}, 'CD267': {'is_create': False, 'links': []}, 'CD268': {'is_create': False, 'links': []}, 'CD269': {'is_create': False, 'links': []}, 'CD270': {'is_create': False, 'links': []}, 'CD271': {'is_create': False, 'links': []}, 'CD272': {'is_create': False, 'links': []}, 'CD273': {'is_create': False, 'links': []}, 'CD274': {'is_create': False, 'links': []}, 'CD275': {'is_create': False, 'links': []}, 'CD276': {'is_create': False, 'links': []}, 'CD277': {'is_create': False, 'links': []}, 'CD278': {'is_create': False, 'links': []}, 'CD279': {'is_create': False, 'links': []}, 'CD280': {'is_create': False, 'links': []}}
LD_use_ids = list(LD_create_link_mapping.keys())
# 是否使用雷达配置
use_LD_config = True
use_LD_count = 100  # 读取 use_LD_count 次数据后更新一次进程间变量

# 车辆模糊对比时需要的其他属性
match_attributes = []  # ['car_type']  # 属性值必须相同
diff_attributes = ['position_id']  # 属性值必须不同

# 创建车辆时，前后允许的最小空闲位置
idle_length = 20

# 全域车辆最大速度
network_max_speed = 30

# 缓冲区长度
buffer_length = 300

# 邻居车牌距离
neighbor_distance = 1000
# 车辆跳跃的最小距离
move_distance = 200

# 平滑处理允许的时间
smoothing_time = 10000  # ms

# 检测到速度后，后续依照此速度行驶的持续时间
reference_time = 15000

# kafka 配置
KAFKA_HOST = '192.168.10.91'
KAFKA_PORT = 9092
send_topic = "MECFUSION"
take_topic = "HolographicRealTimeTarget"

# 仿真精度
accuracy = 7

# 仿真倍速
accemultiples = 1

# after_step 调用频次，即n周期调用一次
after_step_interval = 10

# 左右强制变道的计算周期 10s 一次
change_lane_period = accuracy * 10

# after_one_step 调用频次，即 n 秒调用一次,和周期不一样
after_one_step_interval = 1

# 数据量上限,即下载/上传时路网最大车辆数
max_size = 2500

# 项目目录
BASEPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 路网文件位置
# 路网绘制时 BHX_road_WN_Export10m 按车道被分成两个文件，BHX_ramps_Export10m 被分成前后两段绘制，打断删减形成三个路段
TESSNG_FILE_PATH = os.path.join(BASEPATH, 'Data', "bh_04_23.tess")

# 日志文件位置
log_name = "tessng"
log_level = logging.INFO
LOG_FILE_DIR = os.path.join(BASEPATH, 'Log')

# 路网网格化尺寸
network_grid_size = 20

# 对外暴露的ws端口
WEB_PORT = 8009

# 经纬度转换依据
# p = Proj('+proj=tmerc +lon_0=121.43806548017288 +lat_0=31.243770912743578 +ellps=WGS84')
p = Proj('+proj=tmerc +lon_0=121.41006548017288 +lat_0=31.233770912743578 +ellps=WGS84')

# 北横中心线点位高程文件
CENTER_POINT_PATH = os.path.join(BASEPATH, 'files', 'points_04_23')

car_veh_type_code_mapping = {
    1: 13,  # 轿车
    2: 14,  # SUV
    3: 15,  # 小客面包车
    4: 16,  # 中客、轻客
    5: 17,  # 大客、公交
    6: 18,  # 小型货车
    7: 19,  # 轻型货车
    8: 25,  # 中型货车
    9: 20,  # 重型货车
    10: 21,  # MPV
    11: 26,  # 皮卡
    12: 22,  # 厢式货车
    13: 23,  # 摩托车
    14: 24,  # 其他
}

car_veh_type_name_mapping = {
    1: "轿车",
    2: "SUV",
    3: "小客车",
    4: "中客、轻客",
    5: "大客、公交",
    6: "小型货车",
    7: "轻型货车",
    8: "中型货车",
    9: "重型货车",
    10: "MPV",
    11: "皮卡",
    12: "厢式货车",
    13: "摩托车",
    14: "其他",
}