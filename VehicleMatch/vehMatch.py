# -*- coding: utf-8 -*-
# @Time         : 2022.08.17
# @Author       : Syh
# @Description  : 实现雷达映射车辆的中心线匹配
import copy

from VehicleMatch.geoCalculation import *
from utils.config import LD_link_mapping


def findNewPos(data):
    from MyNet import centerPoint_table
    currentX, currentY, position_id, angle = data['x'], data['y'], data['position_id'], data['angle']
    '''计算雷达映射车辆在TESS车道中心线上的位置

    :param currentX: 传入的待计算新位置的雷达映射车辆的X坐标，单位m
    :param currentY: 传入的待计算新位置的雷达映射车辆的Y坐标，单位m

    :return newRoadId: 新位置对应的路段ID,可能是在连接段上，所以需要特别说明
    :return newLaneId: 新位置对应的车道ID
    :return disInRoad: 新位置在当前路段上的行驶里程
    :return disInNet: 新位置对应在路网中的行驶总里程
    '''
    disInNet, disInRoad = None, None
    currentPos = Point(currentX, currentY)
    minDis, newRoadId, newLaneId = 20, -1, -1  # 最佳匹配点相关属性（距离、路段ID、车道ID）
    for roadId, lanes in centerPoint_table.items():  # 遍历所有road进行路段/连接器匹配
        # if angle is not None:
        #     if roadId in ['L5', 'L43', 'L37', 'L4', 'L3','L39','L15'] and (angle < 45 or angle > 225):
        #         continue
        #     if roadId in ['L6', 'L41', 'L8', 'L9', 'L44', 'L10', 'L21'] and (angle > 45 and angle < 225):
        #         continue
        if int(roadId[1:]) not in LD_link_mapping[data['position_id']]:
            continue

        boundary = lanes[-1]
        if not (boundary['min_x'] <= currentX <= boundary['max_x'] and boundary['min_y'] <= currentY <= boundary['max_y']):
            continue

        for laneId, nodes in enumerate(lanes[:-1]):  # 遍历所有lanes进行车道匹配
            for i in range(len(nodes) - 1):
                laneLine = Line(nodes[i], nodes[i + 1])  # 相邻断点构成一个线段
                ans = pointToLine(currentPos, laneLine)  # 计算当前车辆位置到对应线段的距离（前提垂足落在线段内部）
                if ans and ans[-1] < minDis:  # 该距离小于目前最佳匹配点，更新最佳匹配点
                    disInNet, disInRoad = 0, 0  # 车辆在路网及路段中的行驶里程
                    # 计算在当前路段上的行驶里程
                    for j in range(i):
                        disInRoad += pointDistance(nodes[j], nodes[j + 1])
                    disInRoad += pointDistance(nodes[i], ans[0])  # 车辆在当前路段的行驶里程

                    new_ans_point, minDis = ans
                    newRoadId = roadId
                    newLaneId = laneId
                    newVector = Vector(nodes[i], nodes[i + 1])
                    # 小于1.75m（从中线到车道边线）认为匹配点已经精确到对应车道上
                    if minDis < 1.75:
                        useRoadType, useRoadId = newRoadId[:1], int(newRoadId[1:])
                        return useRoadId, newLaneId, disInRoad, disInNet, useRoadType, new_ans_point, newVector
    # 实在匹配不上，放宽限制
    if minDis < 15:
        useRoadType, useRoadId = newRoadId[:1], int(newRoadId[1:])
        return useRoadId, newLaneId, disInRoad, disInNet, useRoadType, new_ans_point, newVector
    return
