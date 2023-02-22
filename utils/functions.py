# 对所有车辆从车牌，位置间进行匹配，为每两车匹配一个仿真车辆,重新生成所有的轨迹数据
import os
import traceback

from Tessng import *
import time
import collections
import difflib
import numpy as np

import json
from utils.config import neighbor_distance, BASEPATH, laneId_mapping
from scipy.interpolate import interp1d


def diff_cars(veh_infos, cars):
    adjust_cars = {}
    # 先将数据进行初处理，避免同辆车在两位置出现
    for car in cars:
        car_plat = car['plat']
        if not adjust_cars.get(car_plat):
            adjust_cars[car_plat] = car
        else:
            # 调整xy等参数
            adjust_cars[car_plat]['x'] = (adjust_cars[car_plat]['x'] + car['x']) / 2
            adjust_cars[car_plat]['y'] = (adjust_cars[car_plat]['y'] + car['y']) / 2
            adjust_cars[car_plat]['speed'] = (adjust_cars[car_plat]['speed'] + car['speed']) / 2

    combination_list = []  # 匹配成功
    filter_vehs = []
    for veh_info in veh_infos:
        car_plat = veh_info['plat']
        if adjust_cars.get(car_plat):
            combination_list.append([car_plat, veh_info])  # 车牌相同，匹配成功
        else:
            filter_vehs.append(veh_info)
    # 未能匹配成功的 veh，car
    match_plats = [i[0] for i in combination_list]
    filter_cars = {key: value for key, value in adjust_cars.items() if key not in match_plats}
    similar_combination_list, surplus_cars, count = find_close_object(filter_cars, filter_vehs, neighbor_distance)

    new_cars = {}
    for combination in combination_list + similar_combination_list:
        car_plat, veh_info = combination
        # print("new car", veh_info, new_cars, adjust_cars)
        new_cars[veh_info['plat']] = adjust_cars[car_plat]

    for car_plat in surplus_cars:
        new_cars[car_plat] = adjust_cars[car_plat]

    # 最新调整/分配后的轨迹，以及未能匹配上tessng车辆的真实轨迹
    return new_cars, surplus_cars


# 判断两字符是否可视为同一字符串,长度相等且误差值小于等于count
def is_same(s, j, count=1):
    if len(s) != len(j):
        return False
    diff_count = 0
    for index, str in enumerate(s):
        if j[index] != str:
            diff_count += 1
    return bool(diff_count <= count)


def is_same2(s, j):
    if difflib.SequenceMatcher(None, s, j).quick_ratio() > 0.7:
        return True
    return False


def find_close_object(filter_cars, filter_vehs, threshold):
    # 根据车牌，位置，车型等内容为真实车辆匹配仿真车辆
    start_time = time.time()
    points = filter_cars.values()
    neighbor_relationship = find_neighbor_points(points, filter_vehs, threshold)

    # print("find_neighbor_points", (time.time() - start_time) * 1000)
    count = 0
    similar_combination_list, surplus_cars = [], list(filter_cars.keys())
    for plat, veh_infos in neighbor_relationship.items():
        car_type = int(float(filter_cars[plat]['type'] or 13))
        for veh_info in veh_infos:
            count += 1
            # 车型和车牌匹配成功，返回
            # if veh.vehicleTypeCode() == tessng_car_type and is_same(plat, veh.name(), 1):
            if is_same2(plat, veh_info['plat']):
                similar_combination_list.append([plat, veh_info])
                surplus_cars.remove(plat)
                break
    # print('use is_same2',count, (time.time() - start_time) * 1000)
    return similar_combination_list, surplus_cars, count


def find_neighbor_points(points, background_points, threshold):
    """
    寻找当前点周围 X 距离内的其他点
    :param points: 观测点
    :param background_points: 背景点序列
    :param threshold: 距离 X
    :return:
    """
    point_class = collections.defaultdict(list)

    # 为所有背景点分配区间
    for background_point in background_points:
        x_class = int(background_point['x'] // threshold)
        y_class = int(background_point['y'] // threshold)
        point_class[f'{x_class}_{y_class}'].append(background_point)

    distance_mapping = []
    for point in points:
        # print("point", point)
        x_class = int(point['x'] // threshold)
        y_class = int(point['y'] // threshold)

        # 寻找周边区域
        for temp_x_class in [x_class - 1, x_class, x_class + 1]:
            for temp_y_class in [y_class - 1, y_class, y_class + 1]:
                temp_class_name = f"{temp_x_class}_{temp_y_class}"
                # 遍历区域内的所有点，进行计算
                for background_point in point_class[temp_class_name]:
                    distance = np.sqrt(
                        np.square(point['x'] - background_point['x']) + np.square(point['y'] - background_point['y']))

                    # 对于仅id不同的point&background_point, 此处可以通过 revert_distance_name 减少一半的计算量，同时需要去除自身
                    # distance_name = f'{point["id"]}_{background_point["id"]}'
                    distance_mapping.append({
                        'distance': distance,
                        'point': point,
                        'background_point': background_point,
                        'position': {
                            'x': (point['x'] + background_point['x']) / 2,
                            'y': (point['y'] + background_point['y']) / 2,
                        }
                    })

    # 针对性地调整返回值
    neighbor_relationship = collections.defaultdict(list)
    for value in distance_mapping:
        if value['distance'] <= threshold:
            neighbor_relationship[value['point']['plat']].append(value['background_point'])
    return neighbor_relationship


def get_vehi_info(simuiface):
    """
        汽车数据转换
    Args:
        simuiface: TESSNG 路网子接口

    Returns:
        此帧路网中的车辆详情
    """
    data = [
        {
            'positionId': "tessng",
            "timestamp": str(int(time.time() * 1000)),
            "objectAttrFlags": "tessng",
            "objs": []
        }
    ]
    lAllVehi = simuiface.allVehiStarted()
    VehisStatus = simuiface.getVehisStatus()

    VehisStatus_mapping = {
        i.vehiId: i
        for i in VehisStatus
    }

    def get_attr(obj, attr):
        try:
            if obj:
                be_called_function = getattr(obj, attr)
                if callable(be_called_function):
                    return be_called_function()
                else:
                    return be_called_function
        except:
            pass
        return None

    for vehi in lAllVehi:
        vehiStatus = VehisStatus_mapping.get(vehi.id())
        if vehiStatus:
            origin_data = json.loads(vehi.name())
            mPoint = get_attr(vehiStatus, 'mPoint')

            try:
                laneId = laneId_mapping[vehi.lane().link().id()][vehi.lane().number()]
            except:
                error = str(traceback.format_exc())
                print("lane_convert error:", error)
                continue

            origin_data.update(
                {
                    'x': p2m(mPoint.x()),
                    'y': p2m(mPoint.y()),
                    'laneId': laneId,
                    "angleGps": int(get_attr(vehi, 'angle') * 10),
                    "sim_speed": p2m(get_attr(vehi, 'currSpeed')),
                    'lane_number': vehi.lane().number(),
                    'lane_id': vehi.roadId(),
                    'is_link': vehi.roadIsLink(),
                }
            )
            data[0]['objs'].append(origin_data)
    return data

def get_height_funs():
    data = json.load(open(os.path.join(BASEPATH, 'files', 'bh_points.json')))
    lane_code_mapping = {
        "KX1": 0,
        "KX2": 1,
        "KX3": 2,
    }
    height_funs = {}
    for key in ["KX1", "KX2", "KX3"]:
        demo_data = data[key]
        x_list = [i['longitude'] for i in demo_data]
        z_list = [i['z'] for i in demo_data]
        f = interp1d(x_list, z_list, kind='linear', fill_value="extrapolate")
        height_funs[lane_code_mapping[key]] = f
    return height_funs
