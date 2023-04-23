import collections
import json
import os
import logging

from pyproj import Proj

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

# 是否需要对雷达分组
is_groups = False
# 雷达允许创建车辆对应的路段
LD_create_link_mapping = {}
# 雷达映射后可能行驶的路段
LD_create_run_link_mapping = {}
# 对雷达进行分组，同一组内的才会寻找相似车辆(全域追踪)
LD_groups = []

cd_ids = ["CD102", "CD103", "CD104", "CD105", "CD106", "CD107", "CD108", "CD111", "CD112", "CD113", "CD114", "CD115",
       "CD116", "CD117", "CD118", "CD119", "CD120", "CD121", "CD122", "CD123", "CD124", "CD125", "CD126", "CD127",
       "CD128", "CD129", "CD130", "CD131", "CD132", "CD133", "CD134", "CD135", "CD136", "CD137", "CD138", "CD139",
       "CD140", "CD141", "CD142", "CD143", "CD144", "CD145", "CD146", "CD147", "CD148", "CD149", "CD150", "CD151",
       "CD152", "CD153", "CD154", "CD155", "CD156", "CD157", "CD158", "CD159", "CD160", "CD161", "CD162", "CD163",
       "CD201", "CD211", "CD202", "CD203", "CD204", "CD205", "CD206", "CD207", "CD208", "CD209", "CD210", "CD212",
       "CD213", "CD214", "CD215", "CD216", "CD217", "CD218", "CD219", "CD220", "CD221", "CD222", "CD223", "CD224",
       "CD225", "CD226", "CD227", "CD228", "CD229", "CD230", "CD231", "CD232", "CD233", "CD234", "CD235", "CD236",
       "CD237", "CD238", "CD239", "CD240", "CD241", "CD242", "CD243", "CD244", "CD245", "CD246", "CD247", "CD248",
       "CD249", "CD250", "CD251", "CD252", "CD253", "CD254", "CD255", "CD256", "CD257", "CD258", "CD259", "CD260",
       "CD261", "CD262", "CD263", "CD264", "CD265", "CD266", "CD267", "CD268", "CD269", "CD270", "CD271", "CD272",
       "CD273", "CD274", "CD275", "CD276", "CD277", "CD278", "CD279", "CD280", "CGCD1", "CGCD2", "LD41", "CGLD1",
       "CGLD2", "JMDY1", "ZD1", "CGHJ1"]

link_ids = [1, 2, 3, 7, 8, 9, 10, 11, 15, 120, 123, 126, 130, 132, 135]

for cd_id in cd_ids:
    LD_create_link_mapping[cd_id] = link_ids
    LD_create_run_link_mapping[cd_id] = link_ids
LD_groups = [cd_ids]

# 全域雷达的雷达轨迹，允许被映射的路段
LD_group_mapping = {}
for index, group in enumerate(LD_groups):
    for position_id in group:
        run_links = []
        for _ in group:
            run_links += LD_create_run_link_mapping.get(_, [])
        # 每批次的雷达分一组
        LD_group_mapping[position_id] = {"group": group, "index": index, 'run_links': set(run_links)}

# 车辆模糊对比时需要的其他属性
match_attributes = ['car_type']  # 属性值必须相同
diff_attributes = ['position_id']  # 属性值必须不同

# 创建车辆时，前后允许的最小空闲位置
idle_length = 20

# 全域车辆最大速度
network_max_speed = 30

# 缓冲区长度
buffer_length = 300

# 邻居车牌距离
neighbor_distance = 100

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
network_grid_size = 5

# 对外暴露的ws端口
WEB_PORT = 8834

# 经纬度转换依据
# p = Proj('+proj=tmerc +lon_0=121.43806548017288 +lat_0=31.243770912743578 +ellps=WGS84')
p = Proj('+proj=tmerc +lon_0=121.41006548017288 +lat_0=31.233770912743578 +ellps=WGS84')

# 北横中心线点位高程文件
CENTER_POINT_PATH = os.path.join(BASEPATH, 'files', 'points_04_23')

