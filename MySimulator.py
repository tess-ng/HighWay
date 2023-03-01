import json
import random
import sys
import collections
import time
import traceback
from PySide2.QtCore import *
from Tessng import *
from utils.config import buffer_length, smoothing_time, car_veh_type_code_mapping, accuracy, accemultiples, p, \
    after_step_interval, after_one_step_interval
from utils.functions import diff_cars, get_vehi_info
from VehicleMatch.vehMatch import *


new_cars = {}
veh_basic_info = collections.defaultdict(
    lambda: {"lane_number": None, 'limit_numbers': [], 'link_id': None, 'speed': m2p(20),
             'delete': False, 'speeds': [], 'init_time': None})

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
        #计算下一位置完成后处理方法被调用频次
        vehi.setSteps_afterStep(after_step_interval)
        # 确定是否停止车辆运行便移出路网方法调用频次
        vehi.setSteps_isStopDriving(1)
        # #======驾驶行为相关方法调用频次======
        # #重新设置期望速度方法被调用频次
        # vehi.setSteps_reCalcdesirSpeed(1)
        # #计算最大限速方法被调用频次
        # vehi.setSteps_calcMaxLimitedSpeed(1)
        # #计算限制车道方法被调用频次
        # vehi.setSteps_calcLimitedLaneNumber(1)
        # #计算车道限速方法被调用频次
        # vehi.setSteps_calcSpeedLimitByLane(1)
        # #计算安全变道方法被调用频次
        # vehi.setSteps_calcChangeLaneSafeDist(1)
        # #重新计算是否可以左强制变道方法被调用频次
        # vehi.setSteps_reCalcToLeftLane(1)
        # #重新计算是否可以右强制变道方法被调用频次
        # vehi.setSteps_reCalcToRightLane(1)
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

        # 在约定周期内，进行速度较准
        # 超出设定期限后(smoothing_time)重设期望速度  一旦进入仿真，重置期望速度至平均速度
        if veh_basic_info[veh.id()]['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
                veh_basic_info[veh.id()]['init_time'] < smoothing_time:
            ref_inOutSpeed.value = m2p(veh_basic_info[veh.id()]['speed'])
        # 否则采用多段平均速度作为期望速度
        elif veh_basic_info[veh.id()]['speeds'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
                veh_basic_info[veh.id()]['init_time'] < smoothing_time * 10:
            ref_inOutSpeed.value = m2p(np.mean(veh_basic_info[veh.id()]['speeds'][-3:]))
        return True

    def afterStep(self, veh):
        global new_cars, veh_basic_info
        iface = tessngIFace()
        simuiface = iface.simuInterface()
        netiface = iface.netInterface()

        plat = json.loads(veh.name())['plat']
        data = new_cars.get(plat)

        # 没有真实轨迹，不参与计算
        if not data:
            return

        # 匹配成功，删除轨迹
        del new_cars[plat]

        position_car = findNewPos(data['x'], data['y'], data['angle'])
        if not (position_car and position_car[4] == "L"):  # 只能在Link上重置 TODO 如果不是在路段上，设定期望路径
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
        ans = position_car[5]
        real_positon = [ans.x, ans.y]
        sim_position = [p2m(veh.pos().x()), p2m(veh.pos().y())]

        # 计算车辆位置差异与前进方向的余弦值
        driving_direction_vector = position_car[6]  # 行进方向
        real_sim_diff_vector = Vector(Point(*sim_position), Point(*real_positon))  # 仿真向真实趋近
        x = np.array([driving_direction_vector.x, driving_direction_vector.y])  # 仿真车辆所在车道点中心线的向量
        y = np.array([real_sim_diff_vector.x, real_sim_diff_vector.y])  # 真实位置与仿真位置对比向量

        # 方式二: 计算距离采用两位置差异在行进方向上的投影
        projection_scale = np.dot(x, y) / np.dot(x, x)  # 投影比例
        module_x = np.sqrt(np.dot(x, x))  # x的模长
        real_speed = data['origin_speed']
        sim_new_speed = min(max(real_speed + projection_scale * module_x / (smoothing_time / 1000), real_speed / 2), real_speed * 2)

        veh_basic_info[veh.id()].update(
            {
                "speed": sim_new_speed,
                "init_time": simuiface.simuTimeIntervalWithAcceMutiples(),
                'sim': sim_position,
                'real': real_positon,
            }
        )
        veh_basic_info[veh.id()]['speeds'].append(real_speed)

        if abs(projection_scale * module_x) > buffer_length:
            veh_basic_info[veh.id()]['delete'] = True

    # 过载的父类方法，TESS NG 在每个计算周期结束后调用此方法，大量用户逻辑在此实现，注意耗时大的计算要尽可能优化，否则影响运行效率
    def afterOneStep(self):
        print("start_afterOneStep:", time.time())
        global new_index, veh_basic_info, new_cars

        my_process = sys.modules["__main__"].__dict__['myprocess']

        # = == == == == == =以下是获取一些仿真过程数据的方法 == == == == == ==
        # TESSNG 顶层接口
        # TESSNG 顶层接口
        iface = tessngIFace()
        # TESSNG 仿真子接口
        simuiface = iface.simuInterface()
        # TESSNG 路网子接口
        netiface = iface.netInterface()
        # 当前已仿真时间，单位：毫秒
        simuTime = simuiface.simuTimeIntervalWithAcceMutiples()
        lAllVehi = simuiface.allVehiStarted()

        print(simuTime, time.time(), 'all_car:', len(lAllVehi))

        # 当前正在运行车辆列表
        # TODO 实时获取仿真车辆信息,发送至队列
        vehs_data = get_vehi_info(simuiface)
        send_queue = my_process.send_queue
        websocket_queue = my_process.websocket_queue
        try:
            send_queue.put_nowait(vehs_data)
        except:
            print('send_queue is full')

        try:
            websocket_queue.put_nowait(vehs_data)
        except:
            print('websocket_queue is full')

        timestamp = time.time()
        # 每秒执行一次
        if timestamp - my_process.origin_data['timestamp'] < after_one_step_interval:
            return

        try:
            origin_data = my_process.origin_data['data']
            #print('before take', len(origin_data), my_process.origin_data['timestamp'])
            my_process.origin_data['data'] = {}
            my_process.origin_data['timestamp'] = timestamp
        except:
            error = str(traceback.format_exc())
            #print("origin_data get error:", error)
            return

        # 原始数据需要调整, plat 必定存在,所以初始化的车牌必定存在，且作为标准值
        new_frame_data = []
        for plat, i in origin_data.items():
            new_frame_data.append(
                {
                    **i,
                    'plat': plat,
                    'angle': i.get('angleGps') / 10 if i.get('angleGps') is not None else i.get('angleGps'),
                    'origin_speed': i.get('speed', 2000) / 100,
                    'type': i.get('vehType') or 1,
                    'lane_id': i.get('laneId') or 1,
                }
            )

        # 对所有车辆从车牌，位置间进行匹配
        veh_infos = [
            {
                'x': p2m(veh.pos().x()),
                'y': p2m(veh.pos().y()),
                'plat': json.loads(veh.name())['plat'],
                'name': veh.name(),
            } for veh in lAllVehi
        ]
        # 对所有车辆从车牌，位置间进行匹配
        temp_new_cars, surplus_cars = diff_cars(veh_infos, new_frame_data)

        new_cars.update(
            temp_new_cars
        )
        print("middle_afterOneStep:", time.time(), len(temp_new_cars), len(surplus_cars), len(new_frame_data), len(new_cars))
        # 针对没有匹配到tessng车辆的车辆进行发车
        create_car_count = 0
        for plat in surplus_cars:
            data = new_cars[plat]
            del new_cars[plat]

            veh = self.create_car(netiface, simuiface, data)
            if veh:
                # 创建和移除时都会更新字典，时刻保证 radarToTess 与 路网车辆的唯一映射
                self.setStepsPerCall(veh)
                create_car_count += 1
                veh_basic_info[veh.id()].update(
                    {
                        "speed": data['origin_speed'],
                        "init_time": simuiface.simuTimeIntervalWithAcceMutiples(),
                        'sim': [data['x'], data['y']],
                        'real': [data['x'], data['y']],
                    }
                )
                veh_basic_info[veh.id()]['speeds'].append(data['origin_speed'])

        print("end_afterOneStep:", time.time(), "create_car_count:", create_car_count, "car_count", len(lAllVehi))
        return

    def create_car(self, netiface, simuiface, data):
        position_car = findNewPos(data['x'], data['y'], data['angle'])
        # print('find pos use time:', (time.time() - find_pos_start_time) * 1000)
        if position_car and position_car[4] == 'L':  # 只做路段发车
            dvp = Online.DynaVehiParam()
            # TODO 车型，颜色
            dvp.vehiTypeCode = car_veh_type_code_mapping.get(int(float(data.get('type') or 1)), 13)
            dvp.roadId = position_car[0]

            # 重设 lane_number
            lane_id = data.get('lane_id') or 1
            link = netiface.findLink(position_car[0])
            lane_count = len(link.lanes())
            lane_id = max(min(lane_id, lane_count), 1)  # 从 0 开始 输出我就不知道
            lane_number = max(lane_count - lane_id, 0)
            dvp.laneNumber = random.randint(0, 2)  # lane_number
            # if not position_car[4] == 'L':
            #     dvp.toLaneNumber = lane_number
            # print('lane_number', lane_number)
            dvp.dist = position_car[2]
            dvp.speed = data['origin_speed']
            other_json = json.dumps(data)
            dvp.name = other_json
            veh = simuiface.createGVehicle(dvp)
            return veh

    def afterStopVehicle(self, veh):
        if veh.id() in veh_basic_info.keys():
            del veh_basic_info[veh.id()]

        global new_cars
        plat = json.loads(veh.name())['plat']
        if plat in new_cars.keys():
            del new_cars[plat]
        return True

    # def isStopDriving(self, veh):  # 被标记清除的车辆，重新创建
    #     if veh_basic_info[veh.id()]['delete']:
    #         return True
    #     return False
