# -*- coding: utf-8 -*-
# @Time         : 2022.08.16
# @Author       : Syh
# @Description  : TESS路网中心线断点解析所需调用的相关函数

from Tessng import p2m
from VehicleMatch.geoCalculation import *


def getLinkCenterPoints(link):
    '''获取给定Link中各车道的中心线断点序列'''
    lanes = link.lanes()
    nodeInLink = []  # 存储当前Link包含的所有中心线断点，二维列表，每个子列表代表一条车道
    for lane in lanes:
        coords = [[p2m(i.x()), p2m(i.y())] for i in lane.centerBreakPoints()]
        nodes = []  # 储存当前Lane包含的所有中心线断点
        for coord in coords:
            nodes.append(Point(coord[0], coord[1]))
        nodeInLink.append(nodes)
    return nodeInLink

def getConnectorCenterPoints(connector):
    '''获取给定Connector中各车道连接的中心线断点序列'''
    laneConnectors = connector.laneConnectors()
    nodeInConnector = []
    for laneConnector in laneConnectors:
        coords = [[p2m(i.x()), p2m(i.y())] for i in laneConnector.centerBreakPoints()]
        nodes = []
        for coord in coords:
            nodes.append(Point(coord[0], coord[1]))
        nodeInConnector.append(nodes)
    return nodeInConnector

def getConnectorLength(nodeInConnector):
    '''获取选定连接器的长度（Link的长度可以直接通过.length()得到）'''
    connectorLength = 0
    for i in range(len(nodeInConnector) - 1):
        subLength = pointDistance(nodeInConnector[i], nodeInConnector[i + 1])
        connectorLength += subLength
    return connectorLength

def getBoundaryByLink(link):
    x_list = [p2m(point.x()) for point in link.leftBreakPoint3Ds() + link.rightBreakPoint3Ds()]
    y_list = [p2m(point.y()) for point in link.leftBreakPoint3Ds() + link.rightBreakPoint3Ds()]
    return {
        'max_x': max(x_list),
        'min_x': min(x_list),
        'max_y': max(y_list),
        'min_y': min(y_list),
    }

def getBoundaryByConnector(Connector):
    x_list = []
    y_list = []

    for laneConnector in Connector.laneConnectors():
        x_list += [p2m(point.x()) for point in laneConnector.leftBreakPoint3Ds() + laneConnector.rightBreakPoint3Ds()]
        y_list += [p2m(point.y()) for point in laneConnector.leftBreakPoint3Ds() + laneConnector.rightBreakPoint3Ds()]
    return {
        'max_x': max(x_list),
        'min_x': min(x_list),
        'max_y': max(y_list),
        'min_y': min(y_list),
    }
