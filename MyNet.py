# -*- coding: utf-8 -*-

from Tessng import PyCustomerNet, tngPlugin, tessngIFace, m2p, p2m
from VehicleMatch.utils import *
from VehicleMatch.vehMatch import findNewPos

centerPoint_table = dict()  # 地图中所有可行路径的点集合，key为LinkID/ConnectorID，vals为对应点集合——列表最后一个元素为tuple（当前路段长度，当前路段对应总里程)
netTopo_table = dict()  # 地图中路段与连接器的拓朴关系

# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 创建路网
    def createNet(self):
        # 代表TESS NG的接口
        iface = tessngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()

    # 过载的父类方法，当打开网后TESS NG调用此方法
    #     实现的逻辑是：路网加载后获取路段数，如果路网数为0则调用方法createNet构建路网，之后再次获取路段数，如果大于0则启动仿真
    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tessngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # netiface.setSceneSize(3000, 3000)
        # 初始网格化
        netiface.buildNetGrid(5)


        #
        # '''获取路网中所有Link与Connector之间的拓扑关系'''
        # links = netiface.links()
        # connectors = netiface.connectors()
        #
        # # 按照拓扑关系，提取每个独立路径的中心线断点，及对应分段在路网对应的总里程
        # for link in links:
        #     # 当前路段
        #     nodeInLink = getLinkCenterPoints(link)
        #     nodeInLink.append(getBoundaryByLink(link))  # val最后一个元素为tuple(当前路段长度，对应总里程)
        #     centerPoint_table['L' + str(link.id())] = nodeInLink

        # TODO 不在连接段上发车
        # for connector in connectors:
        #     # 当前路段下游连接器
        #     nodeInConnector = getConnectorCenterPoints(connector)
        #     nodeInConnector.append(getBoundaryByConnector(connector))
        #     centerPoint_table['C' + str(connector.id())] = nodeInConnector



        # 下面注释掉的代码逻辑是：通过插件获取传入的配置对象config，从中获取属性'__simuafterload'值，如果等于True值启动仿真
        plugin = tngPlugin()
        config = plugin.tessngConfig()
        if config['__simuafterload'] is True:
            iface.simuInterface().startSimu()
