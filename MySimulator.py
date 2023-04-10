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
    LD_group_mapping, network_max_speed, LD_create_link_mapping, log_name
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
        #重新计算是否可以左强制变道方法被调用频次
        vehi.setSteps_reCalcToLeftLane(change_lane_period)
        #重新计算是否可以右强制变道方法被调用频次
        vehi.setSteps_reCalcToRightLane(change_lane_period)
        # #重新计算是否可以左自由变道方法被调用频次
        # vehi.setSteps_reCalcToLeftFreely(1)
        # # 重新计算是否可以右自由变道方法被调用频次
        # vehi.setSteps_reCalcToRightFreely(1)
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
        global veh_basic_info
        iface = tessngIFace()
        simuiface = iface.simuInterface()
        json_info = veh.jsonInfo()

        # 在约定周期内，进行速度较准
        # 超出设定期限后(smoothing_time)重设期望速度  一旦进入仿真，重置期望速度至平均速度
        # if json_info['speed'] is not None and json_info['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
        #         json_info['init_time'] < smoothing_time:
        #     ref_inOutSpeed.value = m2p(json_info['speed'])
        # # 否则采用多段平均速度作为期望速度
        # elif json_info['speeds'] is not None and json_info['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
        #         json_info['init_time'] < reference_time:
        #     ref_inOutSpeed.value = m2p(np.mean(json_info['speeds'][-3:]))
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

        # TODO 调整为 网格化的移动
        position_id = json_info['position_id']
        locations = netiface.locateOnCrid(QPointF(m2p(data['x']), m2p(data['y'])), 9)
        # 不同雷达只能被允许在部分路段行驶
        # locations = [location for location in locations if location.isLane() and location.castToLane().link().id() in LD_group_mapping[position_id]['run_links']]
        # if not locations:
        #     return
        location = None
        for demo_location in locations:
            if demo_location.pLaneObject.isLane():
                lane_id = demo_location.pLaneObject.castToLane().id()
                link = netiface.findLane(lane_id).link()
                if link.id() in LD_create_link_mapping[position_id]:
                    location = demo_location
                    break
        # locations = [location for location in locations if location.pLaneObject.isLane() and location.pLaneObject.castToLane().link().id() in LD_create_link_mapping[position_id]]
        if not location:
            return

        link = netiface.findLink(position_car[0])
        veh_basic_info[veh.id()]['road_id'] = position_car[0]
        lane_id = data['lane_id']
        if lane_id is not None:
            lane_count = len(link.lanes())
            lane_id = max(min(lane_id, lane_count), 1)  # 为什么用最左侧车道容易崩溃
            lane_number = lane_count - lane_id
            veh_basic_info[veh.id()]['lane_number'] = lane_number
            limit_numbers = [_.number() for _ in link.lanes() if _.number() != lane_number]
            veh_basic_info[veh.id()]['limit_numbers'] = limit_numbers  # 在同一路段上添加车道限行

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
        sim_new_speed = min(max(real_speed + (projection_scale * module_x).tolist() / (smoothing_time / 1000), real_speed / 2),
                            real_speed * 2, network_max_speed)

        # print(sim_position, veh.angle(), angle, x, y, driving_direction_vector, sim_position, real_positon, sim_new_speed, real_speed, projection_scale)
        veh.setJsonProperty('speed', sim_new_speed)
        veh.setJsonProperty('init_time', simuiface.simuTimeIntervalWithAcceMutiples())
        veh.setJsonProperty('sim', sim_position)
        veh.setJsonProperty('real', real_positon)
        veh.setJsonProperty('speeds', json_info.get('speeds', []) + [real_speed])

        # # 不再主动删除车辆
        # if abs(projection_scale * module_x) > buffer_length:
        #     veh_basic_info[veh.id()]['delete'] = True

    # 过载的父类方法，TESS NG 在每个计算周期结束后调用此方法，大量用户逻辑在此实现，注意耗时大的计算要尽可能优化，否则影响运行效率
    def afterOneStep(self):
        logger.info(f"start_afterOneStep: {time.time()}")
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

        logger.info(f"start match {simuTime}, {time.time()}, 'car count:', {len([veh for veh in lAllVehi if veh.isStarted() or not veh.vehicleDriving().getVehiDrivDistance()])}")
        try:
            origin_cars = my_process.origin_data['data']
            my_process.origin_data['data'] = {}
            my_process.origin_data['timestamp'] = timestamp
        except:
            error = str(traceback.format_exc())
            logger.error(f'origin_data get error: {error}')
            return

        # 原始数据需要调整, plat 必定存在,所以初始化的车牌必定存在，且作为标准值
        # new_frame_data = []
        # for plat, i in origin_data.items():
        #     new_frame_data.append(
        #         {
        #             **i,
        #             'plat': plat,
        #             'angle': i.get('angleGps') / 10 if i.get('angleGps') is not None else i.get('angleGps'),
        #             'origin_speed': i.get('speed', 2000) / 100,
        #             'type': i.get('vehType') or 1,
        #             'lane_id': i.get('laneId') or 1,
        #         }
        #     )

        veh_groups = [[]] * len(LD_groups)
        for veh in lAllVehi:  # 已经驶离路网的仍需要被记录，否则可能在末端位置重复创建
            json_info = veh.jsonInfo()

            position_id = json_info['position_id']
            veh_groups[LD_group_mapping[position_id]['index']].append(
                {
                    'x': p2m(veh.pos().x()),
                    'y': p2m(veh.pos().y()),
                    'plat': json_info['plat'],
                    'car_type': json_info['car_type'],
                    'position_id': json_info['position_id'],
                }
            )

        origin_car_groups = [{}] * len(LD_groups)
        for plat, car in origin_cars.items():
            position_id = car['position_id']
            origin_car_groups[LD_group_mapping[position_id]['index']][plat] = car

        create_car_count = 0
        # 车牌匹配时需要考虑雷达分组，只有在同一组内的车辆才会一起进行比较
        for index, _ in enumerate(LD_groups):
            veh_infos = veh_groups[index]
            group_origin_cars = origin_car_groups[index]
            # 对所有车辆从车牌，位置间进行匹配
            new_cars, surplus_cars = diff_cars(veh_infos, group_origin_cars)

            # 针对没有匹配到tessng车辆的车辆进行发车
            for plat in surplus_cars:
                data = new_cars[plat]
                # 只对部分雷达进行发车逻辑
                if data['position_id'] not in LD_create_link_mapping.keys():
                    continue

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

        logger.info(f"end_afterOneStep: {time.time()}, create_car_count: {create_car_count}, car_count: {len([veh for veh in simuiface.allVehicle() if veh.isStarted() or not veh.vehicleDriving().getVehiDrivDistance()])}")
        return

    def create_car(self, netiface, simuiface, data, link_veh_mapping=None):
        link_veh_mapping = link_veh_mapping or {}
        position_id = data['position_id']
        locations = netiface.locateOnCrid(QPointF(m2p(data['x']), m2p(data['y'])), 9)
        # 不同雷达只能被允许在部分路段创建
        location, link = None, None
        for demo_location in locations:
            if demo_location.pLaneObject.isLane():
                lane_id = demo_location.pLaneObject.castToLane().id()
                link = netiface.findLane(lane_id).link()
                if link.id() in LD_create_link_mapping[position_id]:
                    location = demo_location
                    break
        if not (location and link):
            return
        # TODO 判断车辆最近点距离，距离过小时不进行创建,需要取消此逻辑
        disInRoad = location.distToStart
        user_lanes = []
        for lane in link.lanes():
            find = True
            for distance in link_veh_mapping.get(lane.id(), []):  # disInRoad
                if abs(distance - disInRoad) < idle_length:
                    find = False
                    break
            if find:
                user_lanes.append(lane)
        if not user_lanes:
            return

        dvp = Online.DynaVehiParam()
        # TODO 车型，颜色
        dvp.vehiTypeCode = car_veh_type_code_mapping.get(int(float(data['car_type'] or 1)), 13)
        dvp.roadId = link.id()

        # 重设 lane_number
        # lane_id = data.get('lane_id') or 1
        # link = netiface.findLink(position_car[0])
        # lane_count = len(link.lanes())
        # lane_id = max(min(lane_id, lane_count), 1)  # 从 0 开始 输出我就不知道
        # lane_number = max(lane_count - lane_id, 0)

        dvp.laneNumber = choice(user_lanes).number()  # lane_number
        dvp.dist = disInRoad
        dvp.speed = data['origin_speed']
        # other_json = json.dumps(data)
        dvp.name = f"{data['plat']}_{data['position_id']}_{time.time()}"
        veh = simuiface.createGVehicle(dvp)
        return veh

    # def afterStopVehicle(self, veh):
    #     if veh.id() in veh_basic_info.keys():
    #         del veh_basic_info[veh.id()]
    #
    #     # 不需要移除，以为下一个afteronstep会被置空
    #     # global new_cars
    #     # plat = json.loads(veh.name())['plat']
    #     # if plat in new_cars.keys():
    #     #     del new_cars[plat]
    #     return True

    # def isStopDriving(self, veh):  # 被标记清除的车辆，重新创建
    #    if veh_basic_info[veh.id()]['delete']:
    #        return True
    #    return False
