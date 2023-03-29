import os
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

# 雷达允许创建车辆对应的路段
LD_create_link_mapping = {"YP22": [11, 12], "YP2": [6], "YP1": [6], "YP5": [26, 27], "YP7": [8], "YP20": [3, 45],
                          "YP24": [31]}
# 雷达映射后可能行驶的路段
LD_create_run_link_mapping = {"YP22": [11, 12, 13, 14, 15, 39], "YP2": [6, 7, 41], "YP1": [6, 7, 41], "YP5": [26, 27, 28, 29],
                       "YP7": [8, 9, 40, 21, 22, 23, 24, 25, 44, 10], "YP24": [31, 32, 39],
                       "YP20": [4, 5, 34, 37, 17, 18, 19, 20, 43]}

# 对雷达进行分组，同一组内的才会寻找相似车辆 TODO 应当把非创建车辆的雷达也放进来
LD_groups = [["YP22", "YP24"], ["YP2", "YP1"], ["YP5"], ["YP7"], ["YP20"]]

LD_group_mapping = {}
for index, group in enumerate(LD_groups):
    for position_id in group:
        run_links = []
        for _ in group:
            run_links += LD_create_run_link_mapping.get(_, [])

        # 每批次的雷达分一组
        LD_group_mapping[position_id] = {"group": group, "index": index, 'run_links': set(run_links)}


# LD_group_mapping = {LD: {"group": group, "index": index, ''} for index, group in enumerate(LD_groups) for LD in group}
# LD_run_link_mapping = {position_id: set(links) for position_id, links in LD_run_link_mapping.items()}


# LD_run_link_mapping = {}
# # 全域雷达的雷达轨迹，允许被映射的路段


# 车辆需要对比的其他属性
match_attributes = ['car_type']
diff_attributes = ['position_id']

# 创建车辆时，前后允许的最小空闲位置
idle_length = 20

# 全域车辆最大速度
network_max_speed = 25

# 缓冲区长度
buffer_length = 300

# 邻居车牌距离
neighbor_distance = 100

# 平滑处理允许的时间
smoothing_time = 10000  # ms

# 检测到速度后，后续依照此速度行驶的持续时间
reference_time = 15000

# kafka 配置
KAFKA_HOST = '172.16.1.9'
KAFKA_PORT = 9092
send_topic = "MECFUSION"
take_topic = "HolographicRealTimeTarget"

# 仿真精度
accuracy = 5

# after_step 调用频次，即n周期调用一次
after_step_interval = 10

# 左右强制变道的计算周期 10s 一次
change_lane_period = accuracy * 10

# after_one_step 调用频次，即 n 秒调用一次,和周期不一样
after_one_step_interval = 1

# 仿真倍速
accemultiples = 1

# 数据量上限,即下载/上传时路网最大车辆数
max_size = 2500

# 项目目录
BASEPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 路网文件位置
TESSNG_FILE_PATH = os.path.join(BASEPATH, 'Data', "yp_split.tess")

# 日志文件位置
LOG_FILE_DIR = os.path.join(BASEPATH, 'Log')
log_name = "tessng"

# 杨浦大桥经纬度映射关系
p = Proj('+proj=tmerc +lon_0=121.53170529669137 +lat_0=31.26772995795071 +ellps=WGS84')

# 路网网格化尺寸
network_grid_size = 5

# 车道转换函数
laneId_mapping_old = {1: {0: 3, 1: 2, 2: 1}, 2: {0: 3, 1: 2, 2: 1}, 3: {0: 3, 1: 2, 2: 1}, 4: {0: 3, 1: 2, 2: 1},
                      5: {0: 3, 1: 2, 2: 1}, 6: {0: 8, 1: 7, 2: 6}, 7: {0: 8, 1: 7, 2: 6}, 8: {0: 8, 1: 7, 2: 6},
                      9: {0: 8, 1: 7, 2: 6}, 10: {0: 8, 1: 7, 2: 6}, 11: {0: 5, 1: 4}, 12: {0: 5, 1: 4},
                      13: {0: 5, 1: 4},
                      14: {0: 5, 1: 4}, 15: {0: 5, 1: 4}, 16: {0: 5, 1: 4}, 17: {0: 5, 1: 4}, 18: {0: 5, 1: 4},
                      19: {0: 5, 1: 4}, 20: {0: 5, 1: 4}, 21: {0: 10, 1: 9}, 22: {0: 10, 1: 9}, 23: {0: 10, 1: 9},
                      24: {0: 10, 1: 9}, 25: {0: 10, 1: 9}, 26: {0: 10, 1: 9}, 27: {0: 10, 1: 9}, 28: {0: 10, 1: 9},
                      29: {0: 10, 1: 9}, 30: {0: 10, 1: 9}, 31: {0: 2, 1: 1}, 32: {0: 2, 1: 1}, 33: {0: 2, 1: 1},
                      34: {0: 2, 1: 1}, 35: {0: 2, 1: 1}, 37: {0: 3, 1: 2, 2: 1}, 39: {0: 3, 1: 2, 2: 1},
                      40: {0: 8, 1: 7, 2: 6}, 41: {0: 8, 1: 7, 2: 6}, 43: {0: 3, 1: 2, 2: 1}, 44: {0: 8, 1: 7, 2: 6}}

laneId_mapping = {1: {0: 3, 1: 2, 2: 1}, 2: {0: 3, 1: 2, 2: 1}, 3: {0: 3, 1: 2, 2: 1}, 4: {0: 3, 1: 2, 2: 1},
                  5: {0: 3, 1: 2, 2: 1}, 6: {0: 8, 1: 7, 2: 6}, 7: {0: 8, 1: 7, 2: 6}, 8: {0: 8, 1: 7, 2: 6},
                  9: {0: 8, 1: 7, 2: 6}, 10: {0: 8, 1: 7, 2: 6}, 11: {0: 5, 1: 4}, 12: {0: 5, 1: 4}, 13: {0: 5, 1: 4},
                  14: {0: 5, 1: 4}, 15: {0: 5, 1: 4}, 16: {0: 5, 1: 4}, 17: {0: 5, 1: 4}, 18: {0: 5, 1: 4},
                  19: {0: 5, 1: 4}, 20: {0: 5, 1: 4}, 21: {0: 10, 1: 9}, 22: {0: 10, 1: 9}, 23: {0: 10, 1: 9},
                  24: {0: 10, 1: 9}, 25: {0: 10, 1: 9}, 26: {0: 10, 1: 9}, 27: {0: 10, 1: 9}, 28: {0: 10, 1: 9},
                  29: {0: 10, 1: 9}, 30: {0: 10, 1: 9}, 31: {0: 2, 1: 1}, 32: {0: 2, 1: 1}, 33: {0: 2, 1: 1},
                  34: {0: 2, 1: 1}, 35: {0: 2, 1: 1}, 37: {0: 3, 1: 2, 2: 1}, 38: {0: 8, 1: 7, 2: 6},
                  39: {0: 8, 1: 7, 2: 6}, 40: {0: 3, 1: 2, 2: 1}, 41: {0: 8, 1: 7, 2: 6}, 42: {0: 8, 1: 7, 2: 6},
                  43: {0: 3, 1: 2, 2: 1}, 44: {0: 8, 1: 7, 2: 6}, 45: {0: 3, 1: 2, 2: 1}}
