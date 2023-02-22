import json
import collections
from PySide2.QtCore import *
from Tessng import *
from utils.config import buffer_length, smoothing_time, car_veh_type_code_mapping
from utils import diff_cars
from VehicleMatch.vehMatch import *

time_jump=0
new_cars = {}
reverse_radarToTess={}
data = json.load(open('files/北横0211.json', 'r'))


init_position_mapping = data['position_mapping']
temp_car_mapping = data['temp_car_mapping']
position_mapping = {}
for k, v in init_position_mapping.items():
    position_mapping[int(k)] = v
source_timestamps = list(sorted(position_mapping.keys()))

# 当前数据在总数据中的位置
new_index = 0

veh_count_info = collections.defaultdict(lambda: {"sim": 0, "real": 0, 'speed': 20})
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
        self.mSimuCount = 0

    def ref_beforeStart(self, ref_keepOn):
        iface = tessngIFace()
        # 当前路网名
        tmpNetPath = iface.netInterface().netFilePath()
        simuiface = iface.simuInterface()
        simuiface.setSimuAccuracy(5)
        simuiface.setAcceMultiples(10)
        if tmpNetPath != self.mNetPath:
            self.mNetPath = tmpNetPath
            self.mSimuCount = 1
        else:
            self.mSimuCount += 1
        # 可在此设置本次仿真参数
        ref_keepOn.value = True
        # iface = tessngIFace()
        # # TESSNG 仿真子接口
        # simuiface = iface.simuInterface()
        # simuiface.

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
        # #计算下一位置完成后处理方法被调用频次
        # vehi.setSteps_afterStep(1)
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

        # 更新颜色
        if veh_basic_info[veh.id()]['color']:
            veh.setColor(f'#{veh_basic_info[veh.id()]["color"]}')

        # 在约定周期内，进行速度较准
        # 超出设定期限后(smoothing_time)重设期望速度  一旦进入仿真，重置期望速度至平均速度
        # TODO 在beforestep计算期望位置更合理
        if veh_basic_info[veh.id()]['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
                veh_basic_info[veh.id()]['init_time'] < smoothing_time:
            ref_inOutSpeed.value = max(veh_basic_info[veh.id()]['speed'],m2p(10))
        # 否则采用多段平均速度作为期望速度
        elif veh_basic_info[veh.id()]['speeds']:
            ref_inOutSpeed.value = max(np.mean(veh_basic_info[veh.id()]['speeds'][-3:]), m2p(20))
        else:
            ref_inOutSpeed.value=m2p(20)

        # print('speed:', p2m(ref_desirSpeed.value), p2m(veh.currSpeed()), veh_basic_info[veh.id()])
        return True

    # 过载父类方法， 计算车辆当前限制车道序号列表
    # def calcLimitedLaneNumber(self, veh):
    #     global veh_basic_info
    #     iface = tessngIFace()
    #     simuiface = iface.simuInterface()
    #     if veh_basic_info[veh.id()]['init_time'] and simuiface.simuTimeIntervalWithAcceMutiples() - \
    #             veh_basic_info[veh.id()][
    #                 'init_time'] < smoothing_time:
    #         return veh_basic_info[veh.id()]['limit_numbers']
    #     return []
    # def reCalcToRightFreely(self, veh):
    # #def reCalcToRightLane(self, veh):
    #     #if  (not veh.vehiDistRLaneFront() and veh.vehicleFront()) or
    #     if (veh.vehiDistLLaneFront()<veh.vehiDistRLaneFront() and veh.vehiDistFront()<veh.vehiDistRLaneFront() ) and veh.vehiDistFront()<m2p(50) and veh.vehiDistRLaneFront()>m2p(50):
    #         if p2m(veh_basic_info[veh.id()]['speed'])>p2m(veh.currSpeed())+10:
    #             return True
    #     return False
    #
    # def reCalcToLeftFreely(self, veh) :
    # #def reCalcToLeftLane(self, veh):
    #     #if  (not veh.vehiDistLLaneFront() and veh.vehicleFront()) or \
    #     if (veh.vehiDistRLaneFront()<veh.vehiDistLLaneFront() and veh.vehiDistFront()<veh.vehiDistLLaneFront() and veh.vehiDistFront()<m2p(50) and veh.vehiDistLLaneFront()>m2p(50) ):
    #         if p2m(veh_basic_info[veh.id()]['speed'])>p2m(veh.currSpeed())+10:
    #             return True
    #     return False

    def afterStep(self, veh):
        import time
        start_time = time.time()
        global new_cars, veh_basic_info,time_jump
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
        veh_basic_info[veh.id()]['speeds'].append(m2p(data['speed']))
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
        # 缓冲区设置 100米

        # 计算车辆位置差异与前进方向的余弦值
        driving_direction_vector = position_car[6]  # 行进方向
        real_sim_diff_vector = Vector(Point(*sim_position), Point(*real_positon))  # 仿真向真实趋近
        x = np.array([driving_direction_vector.x, driving_direction_vector.y])  # 仿真车辆所在车道点中心线的向量
        y = np.array([real_sim_diff_vector.x, real_sim_diff_vector.y])  # 真实位置与仿真位置对比向量

        # 方式二: 计算距离采用两位置差异在行进方向上的投影
        projection_scale = np.dot(x, y) / np.dot(x, x)  # 投影比例
        module_x = np.sqrt(np.dot(x, x))  # x的模长
        if abs(projection_scale * module_x) > buffer_length:
            veh_basic_info[veh.id()]['delete'] = True
            veh_basic_info[veh.id()]['color'] = 'FFFF00'  # 黄色代表重置
            veh_basic_info[veh.id()]['sim'] = sim_position
            veh_basic_info[veh.id()]['real'] = real_positon
        else:
            real_speed = data['speed']
            sim_new_speed = max(real_speed + projection_scale * module_x / (smoothing_time / 1000), 0)
            veh_basic_info[veh.id()]['speed'] = m2p(sim_new_speed)  # 添加最小最大速度限制
            veh_basic_info[veh.id()][
                'init_time'] = simuiface.simuTimeIntervalWithAcceMutiples()  # 速度重设时的时间
            veh_basic_info[veh.id()]['color'] = '7FFFAA' if projection_scale > 0 else 'FF0000'
        # print('after step use time:', time.time() - start_time)

    # 过载的父类方法，TESS NG 在每个计算周期结束后调用此方法，大量用户逻辑在此实现，注意耗时大的计算要尽可能优化，否则影响运行效率
    def afterOneStep(self):
        import time
        start_time = time.time()
        global new_frame_data, new_index, veh_basic_info, sim_run_time
        # = == == == == == =以下是获取一些仿真过程数据的方法 == == == == == ==
        # TESSNG 顶层接口
        iface = tessngIFace()
        # TESSNG 仿真子接口
        simuiface = iface.simuInterface()
        # TESSNG 路网子接口
        netiface = iface.netInterface()
        # 当前仿真计算批次
        batchNum = simuiface.batchNumber()
        # 当前已仿真时间，单位：毫秒
        simuTime = simuiface.simuTimeIntervalWithAcceMutiples()

        if simuTime % 1000 != 0:
            return

        # 通知主窗体停止仿真
        # self.forStopSimu.emit()
        # 开始仿真的现实时间
        startRealtime = simuiface.startMSecsSinceEpoch()
        # 当前正在运行车辆列表
        lAllVehi = simuiface.allVehiStarted()

        # 之后的 new_frame_data 来自于kafka生成的队列
        sim_run_time = simuiface.simuTimeIntervalWithAcceMutiples()
        use_real_data = False
        for index, timestamp in enumerate(source_timestamps[:-1]):
            if source_timestamps[index] - source_timestamps[0] > sim_run_time:
                break
            # 时间匹配成功，使用真实轨迹(且不是上次使用的轨迹)
            if source_timestamps[index] - source_timestamps[0] < sim_run_time and source_timestamps[index + 1] - \
                    source_timestamps[0] > sim_run_time and index != new_index:

                # 一次性获取25条数据
                new_frame_data = []
                #print("index", index, index + 25, "source_timestamps", source_timestamps[index:index+25])
                for _ in source_timestamps[index:index+25]:
                    new_frame_data += position_mapping[_]

                # new_frame_data = position_mapping[timestamp]
                use_real_data = True
                new_index = index
                break
        # 未到时间，此次不做人工处理变化
        if not use_real_data:
            return

        # TODO 从队列中取数据，取到了就进行匹配,没取到 new_frame_data 为[], new_cars 为 {}
        global new_cars
        new_frame_data = [i for i in new_frame_data if i['plat'] not in ['unknown','' ] ]

        # 对所有车辆从车牌，位置间进行匹配
        new_cars, surplus_cars = diff_cars(lAllVehi, new_frame_data)
        # print('use2', (time.time() - start_time) * 1000)

        # 针对没有匹配到tessng车辆的车辆进行发车
        for plat in surplus_cars:

            data = new_cars[plat]
            #print(data)
            # 没有找到合适的仿真车辆，只能新建
            # find_pos_start_time = time.time()
            # if data['x']>-5200:
            #     dvp = Online.DynaVehiParam()
            #     # TODO 车型，颜色
            #     dvp.vehiTypeCode = car_veh_type_code_mapping.get(int(float(data['type'] or 13)), 13)
            #     dvp.roadId = 516
            #
            #     # 重设 lane_number
            #     lane_id = data['lane_id'] or 1
            #     link = netiface.findLink(303)
            #     lane_count = len(link.lanes())
            #
            #
            #     lane_id = max(min(lane_id, lane_count), 1)  # 从 0 开始 输出我就不知道
            #     lane_number = lane_count - lane_id
            #
            #     dvp.laneNumber = max(lane_number,0)  # lane_number
            #     dvp.dist = 10
            #     dvp.speed = max(data['speed'],20)
            #
            #     other_json = json.dumps(data)
            #     dvp.name = other_json
            #     # dvp.name = data['plat']
            #
            #     createGVehicle_find_pos_start_time = time.time()
            #     veh = simuiface.createGVehicle(dvp)
            #     # print('createGVehicle_find_pos_start_time use time:', (time.time() - createGVehicle_find_pos_start_time) * 1000)
            #     if veh:
            #         # 创建和移除时都会更新字典，时刻保证 radarToTess 与 路网车辆的唯一映射
            #         veh_basic_info[veh.id()]['speed'] = m2p(data['speed'])
            #         reverse_radarToTess[veh.id()] = plat
            #         self.setStepsPerCall(veh)


            position_car = findNewPos(data['x'], data['y'],data['angle'])
            print(position_car,data['x'], data['y'])
            # print('find pos use time:', (time.time() - find_pos_start_time) * 1000)
            if (position_car ):#and position_car[4] == 'L' ):  # 仅支持在link上发车
                # if position_car[0]==238:
                #     print("发车失败：",data['plat'],position_car[0])
                #     break
                dvp = Online.DynaVehiParam()
                # TODO 车型，颜色
                dvp.vehiTypeCode = car_veh_type_code_mapping.get(int(float(data['type'] or 13)), 13)
                dvp.roadId = position_car[0]

                # 重设 lane_number
                lane_id = data['lane_id'] or 1
                link = netiface.findLink(position_car[0])
                lane_count = len(link.lanes())


                lane_id = max(min(lane_id, lane_count), 1)  # 从 0 开始 输出我就不知道
                lane_number = lane_count - lane_id

                dvp.laneNumber = max(lane_number,0)  # lane_number
                dvp.dist = position_car[2]
                dvp.speed = max(data['speed'],20)

                other_json = json.dumps(data)
                dvp.name = other_json
                # dvp.name = data['plat']

                createGVehicle_find_pos_start_time = time.time()
                veh = simuiface.createGVehicle(dvp)
                # print('createGVehicle_find_pos_start_time use time:', (time.time() - createGVehicle_find_pos_start_time) * 1000)
                if veh:
                    # 创建和移除时都会更新字典，时刻保证 radarToTess 与 路网车辆的唯一映射
                    veh_basic_info[veh.id()]['speed'] = m2p(data['speed'])
                    reverse_radarToTess[veh.id()] = plat
                    self.setStepsPerCall(veh)
        # vehs_data = get_vehi_info(simuiface)
        # new_data = []
        # for veh_data in vehs_data['data']:
        #     new_data.append(
        #         {
        #             **veh_data,
        #             'plat': reverse_radarToTess.get(veh_data['id'])
        #
        #         }
        #     )
        # new_data2={'timestamp':sim_run_time,
        #            'data':new_data}
        # json.dump(new_data2, open(f'files/vehs/{sim_run_time}.json', 'w'))
        #print("new_cars count", len(new_cars), "vehs count", len(lAllVehi), "surplus_cars", len(surplus_cars), "new_frame_data", len(new_frame_data), source_timestamps[index])
        #print([json.loads(i.name())['plat'] for i in lAllVehi])
        return

    def afterStop(self):
        # 最多连续仿真2次
        if self.mSimuCount >= 2:
            return
        else:
            self.forReStartSimu.emit()

    def beforeStopVehicle(self, veh):
        veh_basic_info[veh.id()]
        del veh_basic_info[veh.id()]
        return True

    def isStopDriving(self, veh):
        global sim_run_time
        # 被标记清除的车辆，重新创建
        # if veh_basic_info[veh.id()]['delete']:
        #     # print("删除车辆：",veh.name())
        #     # print(veh.name(), veh_basic_info[veh.id()]['sim'], veh_basic_info[veh.id()]['real'])
        #     return True
        return False
# class SimuInterface(Shiboken.Object):
#     def byCpuTime(self):
#         return True
#     def setSimuAccuracy