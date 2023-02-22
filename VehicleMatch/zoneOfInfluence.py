# -*- coding: utf-8 -*-
# @Time         : 2022.08.18
# @Author       : Syh
# @Description  : 根据事故影响区范围确定TESS中的车辆接管区域并判断车辆是否已进入接管区


from VehicleMatch.geoCalculation import *
from Tessng import p2m
from MyNet import centerPoint_table, netTopo_table


def findNodeSequence(roadId, disToFront, range, endPoint):
    '''找到接管区部分覆盖的路段所对应的中心线上的点序列

    :param roadId: 路段ID
    :param disToFront: 接管区在该路段的终点距离路段起点的距离
    :param range: 接管区在该路段上的范围，单位非像素
    :param endPoint: 接管区在该路段的终点坐标（部分覆盖的路段只有两种情况，要么是事故车坐标，要么是接管区最上游路段的终端）

    :return nodeSquence: 对应中心线上的点序列 -> List[Ponit]
    '''
    nodeSquence = []
    radarSpace = disToFront - range  # 接管区上游的雷达映射区长度
    nodeInRoad = centerPoint_table['L' + str(roadId)][-2]  # 路段中心线序列选取最左侧车道

    # 确定接管区在该路段的起点位于哪两个相邻中心线断点之间
    i, j, leftSpace = 0, 1, radarSpace  # 双指针从头遍历中心线断点序列
    subLength = pointDistance(nodeInRoad[i], nodeInRoad[j])  # 相邻中心线断点之间的距离
    while subLength < leftSpace:  # 直到当前中心线分段超出雷达映射区范围
        i += 1
        j += 1
        leftSpace -= subLength
        subLength = pointDistance(nodeInRoad[i], nodeInRoad[j])

    # 找到接管区在该路段上的起点
    startPoint = pointInLine(leftSpace, nodeInRoad[i], nodeInRoad[j])
    nodeSquence.append(startPoint)

    # 确定整个接管区在路段上的点序列
    takeOverSpace = range  # 尚未被nodeSquence覆盖的接管区长度
    subLength = pointDistance(startPoint, nodeInRoad[j])
    while subLength < takeOverSpace and j < len(nodeInRoad) - 1:  # 直到当前中心线分段长度超出接管区范围
        nodeSquence.append(nodeInRoad[j])
        j += 1
        takeOverSpace -= subLength
        subLength = pointDistance(nodeInRoad[j - 1], nodeInRoad[j])
    nodeSquence.append(endPoint)
    return nodeSquence


def findZone(veh, range):
    '''基于事故车位置及给定的影响区范围，确定TESS的接管区域

    :param veh: 事故车（多车事故传入其中一辆即可）-> Tessng.IVehicle
    :param range: 预定义/计算得到的事故影响区长度（在路段上的长度），单位非像素

    :return roadFullContained: 接管区完全覆盖的路段ID -> List
    :return roadPartialContained: 接管区部分覆盖的路段ID -> List[(ID, startPoint, endPoint)]
    '''
    roadFullContained, roadPartialContained = [], []
    roadId = veh.roadId()
    disInRoad = p2m(veh.vehicleDriving().currDistanceInRoad())
    if disInRoad >= range:  # 事故车在当前路段上行驶的里程超过影响区范围，接管区必定包含在当前路段内
        endPoint = Point(p2m(veh.pos().x()), p2m(veh.pos().y()))
        nodeSquence = findNodeSequence(roadId, disInRoad, range, endPoint)
        roadPartialContained.append((roadId, nodeSquence))
    else:  # 事故影响区的范围超过本身路段范围

        # 最下游接管区——事故车所在路段（部分接管）
        endPoint_downS = Point(p2m(veh.pos().x()), p2m(veh.pos().y()))  # 最下游接管区的终端，即事故车所在位置
        NodeSquence_downS = findNodeSequence(roadId, disInRoad, disInRoad, endPoint_downS)  # 最下游路段的接管区
        roadPartialContained.append((roadId, NodeSquence_downS))

        # 中游接管区——影响区完全覆盖的路段（完全接管）
        range -= disInRoad  # 更新尚未被接管的影响区长度
        preId = netTopo_table[roadId][0]
        if preId:  # 排除影响区设置范围超出路网上游范围的情况，即从拓朴表中无法找到上游路段ID
            fullId = 'C' + str(preId)  # 包含Link/Connector标识的完整ID，用于从中心线断点字典中取值
            preLength = centerPoint_table[fullId][-1][0]
            while preLength <= range:  # 事故影响区完全覆盖该路段
                roadFullContained.append(preId)  # 将当前路段ID加入列表
                range -= preLength  # 更新尚未被接管的影响区长度
                # 根据路网拓扑关系找到相邻的上游路段
                if preId in netTopo_table:  # 当前完成判断的路段为Link
                    preId = netTopo_table[preId][0]
                    fullId = 'L' + str(preId)
                    preLength = centerPoint_table[fullId][-1][0]
                else:  # Connector
                    for key, val in netTopo_table.items():
                        if val[1] == preId:
                            preId = key
                            break
                    fullId = 'C' + str(preId)
                    preLength = centerPoint_table[fullId][-1][0]

            # 最上游接管区——影响区影响的最上游路段（部分接管）
            endPoint_upS = centerPoint_table[fullId][-2][-1]  # 最上游接管区的终端，即该路段的末尾断点
            NodeSquence_upS = findNodeSequence(roadId, preLength, range, endPoint_upS)  # 最下游路段的接管区
            roadPartialContained.append((preId, NodeSquence_upS))

    return roadFullContained, roadPartialContained


def isTakeOver(projectionInfo, accidentArea):
    '''判断车辆是否已经进入TESS的接管区

    :param projectionInfo: 待判断的TESS车辆的映射点信息，[[vehPosX, vehPosY], roadId]，单位非像素
    :param accidentArea: 事故影响区范围 -> tuple(roadFullContained, roadPartialContained)
    '''
    vehPos, roadId = projectionInfo[0], projectionInfo[1]
    if roadId in accidentArea[0]:  # 当前车在影响区完全覆盖的路段上
        return True
    else:
        for i in range(len(accidentArea[1])):
            if roadId == accidentArea[1][i][0]:  # 当前车在影响区部分覆盖的路段上
                nodesForMatch = accidentArea[1][i][1]
                for j in range(len(nodesForMatch) - 1):
                    if pointToLine(vehPos, Line(nodesForMatch[j], nodesForMatch[j + 1])):  # 判断当前车的垂足是否在对应中心线段上
                        return True
    return False