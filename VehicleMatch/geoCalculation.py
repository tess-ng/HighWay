# -*- coding: utf-8 -*-
# @Time         : 2022.08.11
# @Author       : Syh
# @Description  : 给定车辆坐标，将其匹配至最近车道中线，返回车辆在对应中线上的匹配点坐标/距离？

'''向量乘法
点乘：a @ b或np.dot(a, b)，数值上为向量对应位置乘积之和|a|*|b|*cos，几何意义为一个向量在另一个向量上投影的长度
叉乘：得到的是个向量，方向为a向量与b向量构成的平面的法线方向（右手准则），模长为|a|*|b|*sin
'''

import numpy as np


class Point(object):
    '''点坐标'''

    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y


class Line(object):
    '''线段——由其两个端点p1, p2表示'''

    def __init__(self, p1, p2) -> None:
        self.p1 = p1
        self.p2 = p2


class Vector(object):
    '''向量——传入两个Point对象'''

    def __init__(self, start, end) -> None:
        self.x = end.x - start.x
        self.y = end.y - start.y


def pointDistance(p1, p2):
    # import pdb;
    # pdb.set_trace()

    '''计算两点之间的距离'''

    # 转换为向量
    v = Vector(p1, p2)

    # 使用np.array表示向量，计算其模长
    t = np.array([v.x, v.y])
    distance = float(np.sqrt(t @ t))  # @表示向量点乘（对应位置相乘之和），数值上为向量模长之积乘以它们之间的夹角余弦值，几何意义为一个向量在另一个向量上的投影长度
    return distance


def pointToLine(C, AB):
    '''计算点C到线段AB的垂足D'''

    # 定义两个向量
    vectorAB = Vector(AB.p1, AB.p2)
    vectorAC = Vector(AB.p1, C)

    # 使用np.array表示向量
    tAB = np.array([vectorAB.x, vectorAB.y])
    tAC = np.array([vectorAC.x, vectorAC.y])

    # 计算向量AD
    tAD = ((tAB @ tAC) / (tAB @ tAB)) * tAB  # 向量ac在向量ab上投影的长度占ab模长的比例（标量），再点乘ab向量，便得到ac在ab上的投影向量ad

    # 得到垂足D
    Dx, Dy = tAD[0] + AB.p1.x, tAD[1] + AB.p1.y
    D = Point(Dx, Dy)

    # 判断D是否在线段AB上
    if min(AB.p1.x, AB.p2.x) <= D.x <= max(AB.p1.x, AB.p2.x) and min(AB.p1.y, AB.p2.y) <= D.y <= max(AB.p1.y, AB.p2.y):
        return D, pointDistance(D, C)
    return False


def pointInLine(length, A, B):
    '''找到线段AB上距离A点length长度的点C坐标'''

    # 定义向量AB
    vectorAB = Vector(A, B)

    # 使用np.array表示向量
    tAB = np.array([vectorAB.x, vectorAB.y])

    # 计算向量AC
    tAC = (length / np.sqrt(tAB @ tAB)) * tAB

    # 得到点C
    Cx, Cy = tAC[0] + A.x, tAC[1] + A.y
    C = Point(Cx, Cy)
    return C
