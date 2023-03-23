# 对所有车辆从车牌，位置间进行匹配，为每两车匹配一个仿真车辆,重新生成所有的轨迹数据

import traceback
import json
import time
import logging
import collections
import difflib
import numpy as np

from Tessng import *
from utils.config import neighbor_distance, laneId_mapping, match_attributes, diff_attributes


def diff_cars(veh_infos, origin_cars):
    # adjust_cars = {car['plat']: car for car in cars}

    combination_list = []  # 匹配成功
    filter_vehs = []
    for veh_info in veh_infos:
        car_plat = veh_info['plat']
        if origin_cars.get(car_plat):
            combination_list.append([car_plat, veh_info])  # 车牌相同，匹配成功
        else:
            filter_vehs.append(veh_info)

    # 未能匹配成功的 veh，car
    match_plats = [i[0] for i in combination_list]
    filter_cars = {key: value for key, value in origin_cars.items() if key not in match_plats}
    similar_combination_list, surplus_cars = find_close_object(filter_cars, filter_vehs, neighbor_distance)

    new_cars = {}
    for combination in combination_list + similar_combination_list:
        car_plat, veh_info = combination
        # print("new car", veh_info, new_cars, adjust_cars)
        new_cars[veh_info['plat']] = origin_cars[car_plat]

    for car_plat in surplus_cars:
        new_cars[car_plat] = origin_cars[car_plat]

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
    if difflib.SequenceMatcher(None, s, j).quick_ratio() > 0.8:
        return True
    return False


def find_close_object(filter_cars, filter_vehs, threshold):
    # 根据车牌，位置，车型等内容为真实车辆匹配仿真车辆
    points = filter_cars.values()
    neighbor_relationship = find_neighbor_points(points, filter_vehs, threshold, match_attributes=match_attributes, diff_attributes=diff_attributes)

    similar_combination_list, surplus_cars = [], list(filter_cars.keys())
    for plat, veh_infos in neighbor_relationship.items():
        # car_type = int(float(filter_cars[plat]['car_type'] or 13))
        for veh_info in veh_infos:
            # 车型和车牌匹配成功，返回
            # if veh.vehicleTypeCode() == tessng_car_type and is_same(plat, veh.name(), 1):
            if is_same2(plat, veh_info['plat']):
                similar_combination_list.append([plat, veh_info])
                surplus_cars.remove(plat)
                break
    return similar_combination_list, surplus_cars


def find_neighbor_points(points, background_points, threshold, match_attributes=None, diff_attributes=None):
    """
    寻找当前点周围 X 距离内的其他点
    :param points: 观测点
    :param background_points: 背景点序列
    :param threshold: 距离 X
    :param other_attributes: 必须确保属性相同
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
        x_class = int(point['x'] // threshold)
        y_class = int(point['y'] // threshold)

        # 寻找周边区域
        for temp_x_class in [x_class - 1, x_class, x_class + 1]:
            for temp_y_class in [y_class - 1, y_class, y_class + 1]:
                temp_class_name = f"{temp_x_class}_{temp_y_class}"
                # 遍历区域内的所有点，进行计算
                for background_point in point_class[temp_class_name]:

                    # 属性均存在但不相等时，取消对比资格(例如车辆类型)
                    is_skip = False
                    for attribute in match_attributes or []:
                        if point.get(attribute) is not None and background_point.get(attribute) is not None and point[attribute] != background_point[attribute]:
                            is_skip = True
                            break
                    # 属性均存在且相等时，取消对比资格(例如针对同一雷达，车牌号必须相等)
                    for attribute in diff_attributes:
                        if point.get(attribute) is not None and background_point.get(attribute) is not None and point[attribute] == background_point[attribute]:
                            is_skip = True
                            break
                    if is_skip:
                        continue

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
    lAllVehi = simuiface.allVehicle()
    VehisStatus = simuiface.getVehisStatus() # 所有正在运行的车辆

    VehisStatus_mapping = {
        i.vehiId: i
        for i in VehisStatus
    }
    link_veh_mapping = collections.defaultdict(list)

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
            origin_data = vehi.jsonInfo()
            mPoint = get_attr(vehiStatus, 'mPoint')

            try:
                laneId = laneId_mapping[vehi.lane().link().id()][vehi.lane().number()]
            except:
                error = str(traceback.format_exc())
                logging.error(f"lane_convert error: {error}")
                # print("lane_convert error:", error)
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
                    'speed': int(p2m(get_attr(vehi, 'currSpeed')) * 100),
                    'plats': vehi.jsonInfo()['plats'],
                }
            )
            data[0]['objs'].append(origin_data)
            if vehi.roadIsLink():  #只记录路段上的车辆，laneId 是唯一的
                link_veh_mapping[vehi.laneId()].append(vehi.vehicleDriving().currDistanceInRoad())
    return data, link_veh_mapping

def lane_convert(veh):  # tess车道编号从0开始
    if veh.roadIsLink():
        #print(veh.road().id(), veh.lane().number())
        return laneId_mapping[veh.road().id()][veh.lane().number()]
    else:
        #print(veh.road().fromLink().id(), veh.lane().number())
        return laneId_mapping[veh.road().fromLink().id()][veh.lane().number()]

