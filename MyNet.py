# -*- coding: utf-8 -*-
from Tessng import PyCustomerNet, tngPlugin, tessngIFace


# 用户插件子类，代表用户自定义与路网相关的实现逻辑，继承自MyCustomerNet
from utils.config import network_grid_size


class MyNet(PyCustomerNet):
    def __init__(self):
        super(MyNet, self).__init__()

    # 过载的父类方法，当打开网后TESS NG调用此方法
    #     实现的逻辑是：路网加载后获取路段数，如果路网数为0则调用方法createNet构建路网，之后再次获取路段数，如果大于0则启动仿真
    def afterLoadNet(self):
        # 代表TESS NG的接口
        iface = tessngIFace()
        # 代表TESS NG的路网子接口
        netiface = iface.netInterface()
        # netiface.setSceneSize(3000, 3000)
        # 初始网格化
        netiface.buildNetGrid(network_grid_size)
