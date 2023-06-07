import datetime
import json
import logging
import random
import sys
import time
import traceback
import numpy as np

from math import cos, sin, pi
from random import choice
from PySide2.QtCore import *
from Tessng import *
from VehicleMatch.geoCalculation import Vector, Point
from utils.config import smoothing_time, car_veh_type_code_mapping, accuracy, accemultiples, \
    after_step_interval, after_one_step_interval, reference_time, idle_length, change_lane_period, LD_groups, \
    LD_group_mapping, network_max_speed, LD_create_link_mapping, log_name, change_lane_frequency
from utils.functions import diff_cars, get_vehi_info
import logging

logger = logging.getLogger(log_name)
new_cars = {}


# 用户插件子类，代表用户自定义与仿真相关的实现逻辑，继承自PyCustomerSimulator
#     多重继承中的父类QObject，在此目的是要能够自定义信号signlRunInfo
class MySimulator(QObject, PyCustomerSimulator):
    signalRunInfo = Signal(str)
    forStopSimu = Signal()
    forReStartSimu = Signal()

    def __init__(self):
        QObject.__init__(self)
        PyCustomerSimulator.__init__(self)

    def ref_beforeStart(self, ref_keepOn):
        iface = tessngIFace()
        simuiface = iface.simuInterface()
        simuiface.setSimuAccuracy(accuracy)
        simuiface.setAcceMultiples(accemultiples)
        # 可在此设置本次仿真参数
        ref_keepOn.value = True

    # 设置本类实现的过载方法被调用频次，即多少个计算周期调用一次。过多的不必要调用会影响运行效率
    def setStepsPerCall(self, vehi):
        # 设置当前车辆及其驾驶行为过载方法被TESSNG调用频次，即多少个计算周调用一次指定方法。如果对运行效率有极高要求，可以精确控制具体车辆或车辆类型及具体场景相关参数
        iface = tessngIFace()
        netface = iface.netInterface()
        netFileName = netface.netFilePath()
        # 范例打开临时路段会会创建车辆方阵，需要进行一些仿真过程控制
        simuface = iface.simuInterface()
        # 仿真精度，即每秒计算次数
        steps = simuface.simuAccuracy()
        # ======设置本类过载方法被TESSNG调用频次，以下是默认设置，可以修改======
        # ======车辆相关方法调用频次======
        # 是否允许对车辆重绘方法的调用
        vehi.setIsPermitForVehicleDraw(False)
        # #计算下一位置前处理方法被调用频次
        # vehi.setSteps_beforeNextPoint(1)
        # #计算下一位置方法方法被调用频次
        # vehi.setSteps_nextPoint(1)
        # 计算下一位置完成后处理方法被调用频次
        vehi.setSteps_afterStep(after_step_interval)
        # 确定是否停止车辆运行便移出路网方法调用频次
        vehi.setSteps_isStopDriving(1)
        # #======驾驶行为相关方法调用频次======
        # #重新设置期望速度方法被调用频次
        vehi.setSteps_reCalcdesirSpeed(after_step_interval)
        # #计算最大限速方法被调用频次
        # vehi.setSteps_calcMaxLimitedSpeed(1)
        # #计算限制车道方法被调用频次
        # vehi.setSteps_calcLimitedLaneNumber(1)
        # #计算车道限速方法被调用频次
        # vehi.setSteps_calcSpeedLimitByLane(1)
        # #计算安全变道方法被调用频次
        # vehi.setSteps_calcChangeLaneSafeDist(1)
        # # 重新计算是否可以左强制变道方法被调用频次
        # vehi.setSteps_reCalcToLeftLane(change_lane_period)
        # # 重新计算是否可以右强制变道方法被调用频次
        # vehi.setSteps_reCalcToRightLane(change_lane_period)
        #重新计算是否可以左自由变道方法被调用频次 tessng车辆的变道本身不受二次开发控制，会有自己的处理逻辑，但是可以使用beforeToLeftFreely去影响
        vehi.setSteps_reCalcToLeftFreely(1)
        # 重新计算是否可以右自由变道方法被调用频次
        vehi.setSteps_reCalcToRightFreely(1)  # change_lane_period
        # #计算跟驰类型后处理方法被调用频次
        # vehi.setSteps_afterCalcTracingType(1)
        # #连接段上汇入到车道前处理方法被调用频次
        # vehi.setSteps_beforeMergingToLane(1)
        # #重新跟驰状态参数方法被调用频次
        # vehi.setSteps_reSetFollowingType(1)
        # 计算加速度方法被调用频次
        vehi.setSteps_calcAcce(1)
        # 重新计算加速度方法被调用频次
        vehi.setSteps_reSetAcce(1)
        # 重置车速方法被调用频次
        vehi.setSteps_reSetSpeed(1)
        # 重新计算角度方法被调用频次
        vehi.setSteps_reCalcAngle(1)
        # vehi.setSteps_recentTimeOfSpeedAndPos(1)
        # vehi.setSteps_travelOnChangingTrace(1)
        # vehi.setSteps_leaveOffChangingTrace(1)
        # #计算后续道路前处理方法被调用频次
        # vehi.setSteps_beforeNextRoad(1)

    def ref_reSetSpeed(self, veh, ref_inOutSpeed):
        iface = tessngIFace()
        simuiface = iface.simuInterface()
        json_info = veh.jsonInfo()

        # 在约定周期内，进行速度较准
        # 超出设定期限后(smoothing_time)重设期望速度  一旦进入仿真，重置期望速度至平均速度
        if json_info['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
                json_info['init_time'] < smoothing_time:
            ref_inOutSpeed.value = m2p(json_info['speed'])
        # 否则采用多段平均速度作为期望速度
        elif json_info['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
                json_info['init_time'] < reference_time:
            ref_inOutSpeed.value = m2p(np.mean(json_info['speeds'][-3:]))
        return True

    def afterStep(self, veh):
        global new_cars
        iface = tessngIFace()
        simuiface = iface.simuInterface()
        netiface = iface.netInterface()

        json_info = veh.jsonInfo()
        plat = json_info['plat']
        data = new_cars.get(plat)

        # 没有真实轨迹，不参与计算
        if not data:
            return
        # 匹配成功，删除轨迹
        del new_cars[plat]

        # 添加被匹配的车牌号
        if data['plat'] not in json_info['plats']:
            veh.setJsonProperty('plats', json_info['plats'] + [data['plat']])

        locations = netiface.locateOnCrid(QPointF(m2p(data['x']), m2p(data['y'])), 9)
        # 不同雷达只能被允许在部分路段行驶
        location = locations and locations[0]

        # TODO 调整为 网格化的移动
        # 在 部分雷达区域直接 移动
        if False:  # location:
            veh.vehicleDriving().move(location.pLaneObject, location.distToStart)
            veh.setJsonProperty('speed', data['origin_speed'])
            veh.setJsonProperty('init_time', simuiface.simuTimeIntervalWithAcceMutiples())
            veh.setJsonProperty('sim', [data['x'], data['y']])
            veh.setJsonProperty('real', [data['x'], data['y']])
            veh.setJsonProperty('speeds', json_info.get('speeds', []) + [data['origin_speed']])
            return

        # # 如果不是在同一路段，直接移动比较合理
        # if location:
        #     # if location.pLaneObject.isLane():
        #     #     lane = location.pLaneObject.castToLane()
        #     # else:
        #     #     lane = location.pLaneObject.castToLaneConnector()
        #     if veh.roadIsLink() and location.pLaneObject.isLane() and veh.roadId() == location.pLaneObject.castToLane().link().id():
        #         # 在同一路段上不move
        #         pass

        # 此处，真实车辆必定在link上
        # 如果仿真车辆不再同一link，直接进行重设 -> 不可取，会导致在路段处大量的跳跃
        # 在路段的起终位置进行映射，其他位置仿真
        real_positon = [data['x'], data['y']]
        sim_position = [p2m(veh.pos().x()), p2m(veh.pos().y())]

        # 计算车辆位置差异与前进方向的余弦值
        angle = (veh.angle() - 90) / 180 * pi
        driving_direction_vector = Vector(Point(0, 0), Point(cos(angle), sin(angle)))  # 行进方向  车头的朝向
        real_sim_diff_vector = Vector(Point(*sim_position), Point(*real_positon))  # 仿真向真实趋近
        x = np.array([driving_direction_vector.x, driving_direction_vector.y])  # 仿真车辆所在车道点中心线的向量
        y = np.array([real_sim_diff_vector.x, real_sim_diff_vector.y])  # 真实位置与仿真位置对比向量

        # 方式二: 计算距离采用两位置差异在行进方向上的投影
        projection_scale = np.dot(x, y) / np.dot(x, x)  # 投影比例
        module_x = np.sqrt(np.dot(x, x))  # x的模长
        real_speed = data['origin_speed']
        sim_new_speed = min(
            max(real_speed + (projection_scale * module_x).tolist() / (smoothing_time / 1000), real_speed / 2),
            real_speed * 2, network_max_speed)

        veh.setJsonProperty('speed', sim_new_speed)
        veh.setJsonProperty('init_time', simuiface.simuTimeIntervalWithAcceMutiples())
        veh.setJsonProperty('sim', sim_position)
        veh.setJsonProperty('real', real_positon)
        veh.setJsonProperty('speeds', json_info.get('speeds', []) + [real_speed])

    # 过载的父类方法，TESS NG 在每个计算周期结束后调用此方法，大量用户逻辑在此实现，注意耗时大的计算要尽可能优化，否则影响运行效率
    def afterOneStep(self):
        global new_cars

        my_process = sys.modules["__main__"].__dict__['myprocess']

        # = == == == == == =以下是获取一些仿真过程数据的方法 == == == == == ==
        # TESSNG 顶层接口
        iface = tessngIFace()
        # TESSNG 仿真子接口
        simuiface = iface.simuInterface()
        # TESSNG 路网子接口
        netiface = iface.netInterface()
        # 当前已仿真时间，单位：毫秒
        simuTime = simuiface.simuTimeIntervalWithAcceMutiples()
        logger.info(f"simuTime:{simuTime},  start_afterOneStep: {time.time()}")
        lAllVehi = simuiface.allVehicle()

        # 当前正在运行车辆列表
        vehs_data, link_veh_mapping = get_vehi_info(simuiface)
        send_queue = my_process.send_queue
        websocket_queue = my_process.websocket_queue
        try:
            send_queue.put_nowait(vehs_data)
        except:
            logger.warning('send_queue is full')

        try:
            websocket_queue.put_nowait(vehs_data)
        except:
            logger.warning('websocket_queue is full')

        timestamp = time.time()
        # 每n秒执行一次
        if timestamp - my_process.origin_data['timestamp'] < after_one_step_interval:
            return

        logger.info(
            f"start match {simuTime}, {time.time()}, 'car count:', {len([veh for veh in lAllVehi if veh.isStarted() or not veh.vehicleDriving().getVehiDrivDistance()])}")
        try:
            origin_cars = my_process.origin_data['data']
            my_process.origin_data['data'] = {}
            my_process.origin_data['timestamp'] = timestamp
        except:
            error = str(traceback.format_exc())
            logger.error(f'origin_data get error: {error}')
            return

        veh_groups = [[]]
        for veh in lAllVehi:  # 已经驶离路网的仍需要被记录，否则可能在末端位置重复创建
            json_info = veh.jsonInfo()
            veh_groups[0].append(
                {
                    'x': p2m(veh.pos().x()),
                    'y': p2m(veh.pos().y()),
                    'plat': json_info['plat'],
                    'car_type': json_info['car_type'],
                    'position_id': json_info['position_id'],
                }
            )

        origin_car_groups = [{}]
        for plat, car in origin_cars.items():
            origin_car_groups[0][plat] = car

        create_car_count = 0
        # 车牌匹配时需要考虑雷达分组，只有在同一组内的车辆才会一起进行比较
        for index, _ in enumerate([[]]):
            veh_infos = veh_groups[index]
            group_origin_cars = origin_car_groups[index]
            # 对所有车辆从车牌，位置间进行匹配
            new_cars, surplus_cars = diff_cars(veh_infos, group_origin_cars)

            # 针对没有匹配到tessng车辆的车辆进行发车
            for plat in surplus_cars:
                data = new_cars[plat]
                veh = self.create_car(netiface, simuiface, data, link_veh_mapping)
                if veh:
                    del new_cars[plat]
                    # 创建和移除时都会更新字典，时刻保证 radarToTess 与 路网车辆的唯一映射
                    self.setStepsPerCall(veh)
                    # 设置属性
                    data.update(
                        {
                            "speed": data['origin_speed'],  # TODO 暂时取消1.5倍的加速
                            "init_time": simuiface.simuTimeIntervalWithAcceMutiples(),
                            'sim': [data['x'], data['y']],
                            'real': [data['x'], data['y']],
                            'plats': [plat],
                            'speeds': [data['origin_speed']],
                        }
                    )
                    veh.setJsonInfo(data)
                    create_car_count += 1
                    link_veh_mapping[veh.laneId()].append(veh.vehicleDriving().currDistanceInRoad())

            logger.info(
                f"end_afterOneStep: {time.time()}, create_car_count: {create_car_count}, origin_cars_count: {len(group_origin_cars)},  surplus_cars: {len(surplus_cars)}, car_count: {len([veh for veh in simuiface.allVehicle() if veh.isStarted() or not veh.vehicleDriving().getVehiDrivDistance()])}")
        return

    def create_car(self, netiface, simuiface, data, link_veh_mapping=None):
        locations = netiface.locateOnCrid(QPointF(m2p(data['x']), m2p(data['y'])), 9)
        if not locations:
            return

        # 车辆允许在任何地方被创建
        location = locations[0]
        dvp = Online.DynaVehiParam()
#        if location.pLaneObject.isLane():
#            lane = location.pLaneObject.castToLane()
#            dvp.roadId = lane.link().id()
#            dvp.laneNumber = lane.number()
#        else:
#            lane_connector = location.pLaneObject.castToLaneConnector()
#            dvp.roadId = lane_connector.connector().id()
#            dvp.laneNumber = lane_connector.fromLane().number()
#            dvp.toLaneNumber = lane_connector.toLane().number()
#
        # TODO 根据前端传入的车道编号创建车辆，只在路段上进行发车
        dvp.vehiTypeCode = car_veh_type_code_mapping.get(int(float(data['car_type'] or 1)), 13)
        dvp.dist = location.distToStart
        dvp.speed = data['origin_speed']
        dvp.name = f"{data['plat']}_{data['position_id']}_{time.time()}"
        for location in locations:
            if not location.pLaneObject.isLane():
                continue
            lane = location.pLaneObject.castToLane()
            link = lane.link()
            lane_number = len(link.lanes()) - data['lane_id']
            # 找到了合适的车道，进行发车
            if lane_number >= 0:
                dvp.roadId = link.id()
                dvp.laneNumber = lane_number
                veh = simuiface.createGVehicle(dvp)
                return veh

    # 计算是否有权利进行左右自由变道,降低变道频率
    def ref_beforeToLeftFreely(self, veh, ref_keepOn):
        # 降低变道频率,change_lane_frequency 越小，禁止计算是否自由变道的可能性越大
        if random.random() > change_lane_frequency:
            ref_keepOn.value = False
        return None

    def ref_beforeToRightFreely(self, veh, ref_keepOn):
        # 降低变道频率,change_lane_frequency 越小，禁止计算是否自由变道的可能性越大
        if random.random() > change_lane_frequency:
            ref_keepOn.value = False
        return None

    # 添加车道限行
    def calcLimitedLaneNumber(self, veh):
        limit_lanes = []
        if veh.roadIsLink():
            lane_id = veh.jsonInfo()['lane_id']  # lane_id 必定存在
            run_lane = veh.lane()
            link = run_lane.link()
            lane_number = len(link.lanes()) - lane_id
            if lane_number >= 0:
                limit_lanes = [lane.number() for lane in run_lane.link().lanes() if lane.number() != lane_number]

            # logger.info(f'车道限行: lane_number: {run_lane.number()}, lane_id: {lane_id}, limit: {limit_lanes}, run_number: {lane_number}')
        return limit_lanes