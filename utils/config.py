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

# TODO 北横应该分双向就可以了
# 雷达允许创建车辆对应的路段
LD_create_link_mapping = {}
# 雷达映射后可能行驶的路段
LD_create_run_link_mapping = {}
# 对雷达进行分组，同一组内的才会寻找相似车辆(全域追踪) TODO 只要双向分两组就可以
LD_groups = []
# 全域雷达的雷达轨迹，允许被映射的路段
LD_group_mapping = {}
for index, group in enumerate(LD_groups):
    for position_id in group:
        run_links = []
        for _ in group:
            run_links += LD_create_run_link_mapping.get(_, [])
        # 每批次的雷达分一组
        LD_group_mapping[position_id] = {"group": group, "index": index, 'run_links': set(run_links)}

# 车辆对比时需要的其他属性
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
TESSNG_FILE_PATH = os.path.join(BASEPATH, 'Data', "bh.tess")

# 日志文件位置
log_name = "tessng"
log_level = logging.INFO
LOG_FILE_DIR = os.path.join(BASEPATH, 'Log')

# 北横中心线点位搞成文件
CENTER_POINT_PATH = os.path.join(BASEPATH, 'files', 'bh_points.json')

# 路网网格化尺寸
network_grid_size = 5

WEB_PORT = 8009

p = Proj('+proj=tmerc +lon_0=121.43806548017288 +lat_0=31.243770912743578 +ellps=WGS84')
