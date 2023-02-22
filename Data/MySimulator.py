import json
import sys
import collections
import time

from PySide2.QtCore import *
from Tessng import *
from utils.config import buffer_length, smoothing_time, car_veh_type_code_mapping, accuracy,accemultiples
from utils import diff_cars, get_vehi_info
from VehicleMatch.vehMatch import *

# time_jump=0
new_cars = {}
# global_vehs = []


veh_basic_info = collections.defaultdict(
    lambda: {"lane_number": None, 'limit_numbers': [], 'link_id': None, 'speed': m2p(20), "is_change": False,
             'color': None,
             'delete': False, 'speeds': [], 'init_time': None})

diff_info = {"right": 0, 'left': 0, 'all': 0}


# 用户插件子类，代表用户自定义与仿真相关的实现逻辑，继承自PyCustomerSimulator
#     多重继承中的父类QObject，在此目的是要能够自定义信号signlRunInfo
class MySimulator(QObject, PyCustomerSimulator):
    signalRunInfo = Signal(str)
    forStopSimu = Signal()
    forReStartSimu = Signal()

    def __init__(self):
        QObject.__init__(self)
        PyCustomerSimulator.__init__(self)
        # 车辆方阵的车辆数
        self.mrSquareVehiCount = 28
        # 飞机速度，飞机后面的车辆速度会被设定为此数据
        self.mrSpeedOfPlane = 0
        # 当前正在仿真计算的路网名称
        self.mNetPath = None
        # 相同路网连续仿真次数
        # self.mSimuCount = 0

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
        #======设置本类过载方法被TESSNG调用频次，以下是默认设置，可以修改======
        #======车辆相关方法调用频次======
        #是否允许对车辆重绘方法的调用
        vehi.setIsPermitForVehicleDraw(False)
        # #计算下一位置前处理方法被调用频次
        # vehi.setSteps_beforeNextPoint(1)
        # #计算下一位置方法方法被调用频次
        # vehi.setSteps_nextPoint(1)
        # #计算下一位置完成后处理方法被调用频次
        # vehi.setSteps_afterStep(1)
        #确定是否停止车辆运行便移出路网方法调用频次
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
        #计算加速度方法被调用频次
        vehi.setSteps_calcAcce(1)
        # 重新计算加速度方法被调用频次
        vehi.setSteps_reSetAcce(1)
        #重置车速方法被调用频次
        vehi.setSteps_reSetSpeed(1)
        #重新计算角度方法被调用频次
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

        # 更新颜色
        # if veh_basic_info[veh.id()]['color']:
        #     veh.setColor(f'#{veh_basic_info[veh.id()]["color"]}')

        # 在约定周期内，进行速度较准
        # 超出设定期限后(smoothing_time)重设期望速度  一旦进入仿真，重置期望速度至平均速度
        # TODO 在beforestep计算期望位置更合理
        # print(veh_basic_info[veh.id()]['init_time'], simuiface.simuTimeIntervalWithAcceMutiples())
        if veh_basic_info[veh.id()]['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
                veh_basic_info[veh.id()]['init_time'] < smoothing_time:
            ref_inOutSpeed.value = max(veh_basic_info[veh.id()]['speed'],m2p(10))
        # 否则采用多段平均速度作为期望速度
        elif veh_basic_info[veh.id()]['speeds']:
            ref_inOutSpeed.value = max(np.mean(veh_basic_info[veh.id()]['speeds'][-3:]), m2p(20))
        else:
            ref_inOutSpeed.value = m2p(20)
        return True

    def afterStep(self, veh):
        global new_cars, veh_basic_info
        iface = tessngIFace()
        simuiface = iface.simuInterface()
        netiface = iface.netInterface()

        plat = json.loads(veh.name())['plat']
        data = new_cars.get(plat)

        if not data:
            veh_basic_info[veh.id()]['color'] = 'FFC0CB'
            # 没有真实轨迹，不参与计算
            return

        veh_basic_info[veh.id()]['color'] = None
        veh_basic_info[veh.id()]['speeds'].append(m2p(data['origin_speed']))
        veh_basic_info[veh.id()]['color'] = 'FFFFFF'  # 至少找到了，不用当黑户，白色

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
        sim_new_speed = max(real_speed + projection_scale * module_x / (smoothing_time / 1000), 0)
        veh_basic_info[veh.id()]['speed'] = m2p(sim_new_speed)  # 添加最小最大速度限制
        veh_basic_info[veh.id()]['init_time'] = simuiface.simuTimeIntervalWithAcceMutiples()  # 速度重设时的时间
        veh_basic_info[veh.id()]['color'] = '7FFFAA' if projection_scale > 0 else 'FF0000'

        if abs(projection_scale * module_x) > buffer_length:
            veh_basic_info[veh.id()]['delete'] = True
            veh_basic_info[veh.id()]['color'] = 'FFFF00'  # 黄色代表重置

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
        if send_queue.full():
            send_queue.get()
        send_queue.put(vehs_data)
        take_queue = my_process.take_queue

        origin_data = {}
        for i in range(25 // accuracy):  # TODO 仿真精度调整为1次/s,需要匹配着获取数据,对方数据为 20/s
            # 此处会浪费大量时间，估计取一次数据需要 1ms
            try:
                radar_data = take_queue.get_nowait()
                objs = radar_data.get('objs', [])
                for obj in objs:
                    if obj.get("vehPlateString"):
                        origin_data[obj['vehPlateString']] = obj
            except:
                break

        # 原始数据需要调整
        new_frame_data = []
        for i in origin_data.values():
            if 'longitude' not in i.keys() or 'latitude' not in i.keys() or 'vehPlateString' not in i.keys():
                continue
            if i['vehPlateString'] not in ['unknown', '']:
                new_frame_data.append(
                    {
                        **i,
                        'plat': i['vehPlateString'],
                        'x': (i['longitude'] / 10000000 +0.0002 - 121.55412756) * 101938.87057335733+1300.9,
                        'y': -((i['latitude'] / 10000000 - 31.24923271)* 118402.7483190337 -1234.61),
                        'angle': i.get('angleGps') / 10 if i.get('angleGps') is not None else i.get('angleGps'),
                        'origin_speed': i.get('speed', 2000) / 100,
                        'type': i.get('vehType') or 1,
                        'lane_id': i.get('laneId') or 1,
                    }
                )

        # new_frame_data = [i for i in new_frame_data if i['plat'] != 'unknown' and i['plat'] == '沪BZU125']
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
        new_cars, surplus_cars = diff_cars(veh_infos, new_frame_data)
        print("middle_afterOneStep:", time.time(), len(new_cars), len(surplus_cars), len(veh_infos))
        # 针对没有匹配到tessng车辆的车辆进行发车
        create_car_count = 0
        for plat in surplus_cars:
            data = new_cars[plat]
            # 没有找到合适的仿真车辆，只能新建
            position_car = findNewPos(data['x'], data['y'], data['angle'])
            if (position_car and position_car[4] == 'L'):  # 仅支持在link上发车
                dvp = Online.DynaVehiParam()
                # TODO 车型，颜色
                dvp.vehiTypeCode = car_veh_type_code_mapping.get(int(float(data['type'] or 13)), 13)
                dvp.roadId = position_car[0]

                # 重设 lane_number
                lane_id = data['lane_id'] or 1
                link = netiface.findLink(position_car[0])
                lane_count = len(link.lanes())
                if dvp.roadId in [22, 21, 24, 25, 26, 238, 27, 28]:  # 6,7,8
                    lane_id = lane_id - 5
                elif dvp.roadId in [32, 31, 29]:  # 9,10
                    lane_id = lane_id - 8
                elif dvp.roadId == 33:  # 6,7
                    lane_id = lane_id - 5
                elif dvp.roadId in [18, 16, 15, 14, 10, 11, 12]:  # 1,2,3
                    lane_id = lane_id
                elif dvp.roadId in [20, 34]:  # 4,5
                    lane_id = lane_id - 3
                lane_id = max(min(lane_id, lane_count), 1)  # 从 0 开始 输出我就不知道
                lane_number = lane_count - lane_id
                dvp.laneNumber = max(lane_number, 0)  # lane_number

                dvp.laneNumber = lane_number  # lane_number
                dvp.dist = position_car[2]
                dvp.speed = max(data['origin_speed'], 20)  # TODO 是否需要用速度

                other_json = json.dumps(data)
                dvp.name = other_json  # data['plat']
                veh = simuiface.createGVehicle(dvp)
                if veh:
                    self.setStepsPerCall(veh)
                    create_car_count += 1
        print("end_afterOneStep:", time.time(), "create_car_count:", create_car_count)
        return

    # # 过载的父类方法， 初始化车辆，在车辆启动上路时被TESS NG调用一次
    # def initVehicle(self, vehi):
    #     #设置当前车辆及其驾驶行为过载方法被TESSNG调用频次，即多少个计算周调用一次指定方法。如果对运行效率有极高要求，可以精确控制具体车辆或车辆类型及具体场景相关参数
    #     self.setStepsPerCall(vehi)

    def afterStopVehicle(self, veh):
        if veh.id() in veh_basic_info.keys():
            del veh_basic_info[veh.id()]
        return True

    def isStopDriving(self, veh):        # 被标记清除的车辆，重新创建
        if veh_basic_info[veh.id()]['delete']:
            return True
        return False

