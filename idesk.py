#!/usr/bin/python
# -*- coding:utf-8 -*-
import snap7.client as s7client
import snap7.snap7types as s7type
import logging
from threading import Timer
import struct
import json
import interface
import time
import paho.mqtt.client

# {
#             "index": 1,
#             "ip": "10.35.121.101",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 2,
#             "ip": "10.35.121.102",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 3,
#             "ip": "10.35.121.103",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 4,
#             "ip": "10.35.121.104",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 5,
#             "ip": "10.35.121.105",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 6,
#             "ip": "10.35.121.106",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 7,
#             "ip": "10.35.121.107",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 8,
#             "ip": "10.35.121.108",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 9,
#             "ip": "10.35.121.109",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 10,
#             "ip": "10.35.121.110",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 11,
#             "ip": "10.35.121.111",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 12,
#             "ip": "10.35.121.112",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 13,
#             "ip": "10.35.121.113",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 14,
#             "ip": "10.35.121.114",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 15,
#             "ip": "10.35.121.115",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 16,
#             "ip": "10.35.121.116",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 17,
#             "ip": "10.35.121.117",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 18,
#             "ip": "10.35.121.118",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 19,
#             "ip": "10.35.121.119",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 20,
#             "ip": "10.35.121.120",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 21,
#             "ip": "10.35.121.121",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 22,
#             "ip": "10.35.121.122",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 23,
#             "ip": "10.35.121.123",
#             "rack": 0,
#             "slot": 1
#         },
#         {
#             "index": 24,
#             "ip": "10.35.121.124",
#             "rack": 0,
#             "slot": 1
#         },


class ButtonStatus(object):
    def __init__(self):
        self.green = False
        self.red = False


class LampStatus(object):
    def __init__(self):
        self.green = False
        self.red = False
        self.yellow = False
        self.beep = False


class PowerMeter(object):
    def __init__(self):
        self.phaseA_voltage = 0
        self.phaseA_current = 0
        self.Power_active = 0
        self.Power_reactive = 0
        self.Power_total = 0
        self.Power_factor = 0


class Sensor(object):
    def __init__(self):
        self.temperature = 0.0
        self.humidity = 0.0
        self.optical = False


class iDesk(object):
    def __init__(self, ip, rack, slot, reconnect_period, collect_period, index):
        # 复位变量
        self.buttonStatus = ButtonStatus()
        self.lampStatus = LampStatus()
        self.powerMeter = PowerMeter()
        self.sensor = Sensor()
        self.fanStatus = False

        # client
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = s7client.Client()
        self.reconnect_period = reconnect_period
        self.collect_period = collect_period
        self.index = index
        self.name = "iDesk" + str(self.index)

        self.isFinished = False
        self.lesson = 0
        # mqtt interface
        self.interface = interface.iMQTT('IR829/' + str(self.index) + '/TX', self.name)

    # 周期性检查设备连接情况，如果异常则重连
    def reconnect(self):
        if not self.client.get_connected():
            logging.info('--reconnect-- Client :%d disconnected! (%s)' % (self.index, self.ip))
            try:
                self.client.disconnect()
                self.client.connect(self.ip, rack=self.rack, slot=self.slot)
            except Exception as e:
                logging.error(str(e))
        else:
            logging.debug("--reconnect-- Client %s connected!" % self.ip)
        t = Timer(self.reconnect_period, self.reconnect)
        t.start()

    # 周期性读取数据
    def collect(self):
        if self.client.get_connected():
            try:
                # I0.0 光纤输入
                # I0.1 红色按钮 常闭
                # I0.2 绿色按钮 常开
                io_input = self.client.read_area(s7type.S7AreaPE, 0, 0, 1)
                logging.debug("PE input "+ str(io_input))
                if io_input[0] & 0x04 != 0:
                    self.buttonStatus.green = True
                else:
                    self.buttonStatus.green = False
                if io_input[0] & 0x02 != 0:
                    self.buttonStatus.red = True
                else:
                    self.buttonStatus.red = False
                if io_input[0] & 0x01 != 0:
                    self.sensor.optical = True
                else:
                    self.sensor.optical = False
                # Q0.0 红灯
                # Q0.1 绿灯
                # Q0.2 黄灯
                # Q0.3 蜂鸣器
                # Q0.4 风扇
                io_output = self.client.read_area(s7type.S7AreaPA, 0, 0, 2)
                logging.debug("PA input " + str(io_output))
                if io_output[0] & 0x01:
                    self.lampStatus.red = True
                else:
                    self.lampStatus.red = False
                if io_output[0] & 0x02:
                    self.lampStatus.green = True
                else:
                    self.lampStatus.green = False
                if io_output[0] & 0x04:
                    self.lampStatus.yellow = True
                else:
                    self.lampStatus.yellow = False
                if io_output[0] & 0x08:
                    self.lampStatus.beep = True
                else:
                    self.lampStatus.beep = False
                if io_output[0] & 0x10:
                    self.fanStatus = True
                else:
                    self.fanStatus = False
        #         # MD16 温度
        #         # MD24 湿度
        #         memory_sensor = self.client.read_area(s7type.S7AreaMK, 0, 16, 16)
        #         # buffer转float
        #         # !!!特别关键
        #         self.sensor.temperature = struct.unpack_from('>f', memory_sensor, 0)[0]
        #         self.sensor.humidity = struct.unpack_from('>f', memory_sensor, 4)[0]
        #         # 读电表数据
        #         # MD38 电压
        #         # MD42 电流
        #         meter_data = self.client.read_area(s7type.S7AreaMK, 0, 38, 16)
        #         # buffer转float
        #         # !!!特别关键
        #         self.powerMeter.phaseA_voltage = struct.unpack_from('>f', meter_data, 0)[0]
        #         self.powerMeter.phaseA_current = struct.unpack_from('>f', meter_data, 4)[0]
        #
        #         # 读编号
        #         # MB80
        #         self.lesson = self.client.read_area(s7type.S7AreaMK, 0, 80, 1)
        #         # 读完成标志
        #         # M90.0
        #         m90data = self.client.read_area(s7type.S7AreaMK, 0, 90, 1)
        #         if m90data & 0x01:
        #             self.isFinished = True
        #         else:
        #             self.isFinished = False
        #
        #         # meter_data = self.client.read_area(s7type.S7AreaDB, 9, 0, 48)
        #         # self.powerMeter.phaseA_voltage = struct.unpack_from('>f', meter_data, 0)[0]
        #         # self.powerMeter.phaseA_current = struct.unpack_from('>f', meter_data, 4)[0]
        #         # self.powerMeter.Power_active = struct.unpack_from('>f', meter_data, 8)[0] * 1000
        #         # self.powerMeter.Power_reactive = struct.unpack_from('>f', meter_data, 12)[0] * 1000
        #         # self.powerMeter.Power_total = struct.unpack_from('>f', meter_data, 16)[0] * 1000
        #         # self.powerMeter.Power_factor = struct.unpack_from('>f', meter_data, 20)[0]
        #
        #         # send to redis
        #         # cache.cache_save("中工创智:%s:按键:green" % self.id, self.buttonStatus.green, None)
        #         # cache.cache_save("中工创智:%s:按键:red" % self.id, self.buttonStatus.red, None)
        #         # cache.cache_save("中工创智:%s:灯:green" % self.id, self.lampStatus.green, None)
        #         # cache.cache_save("中工创智:%s:灯:red" % self.id, self.lampStatus.red, None)
        #         # cache.cache_save("中工创智:%s:灯:yellow" % self.id, self.lampStatus.yellow, None)
        #         # cache.cache_save("中工创智:%s:灯:beep" % self.id, self.lampStatus.beep, None)
        #         # cache.cache_save("中工创智:%s:风扇" % self.id, self.fanStatus, None)
        #         # cache.cache_save("中工创智:%s:传感器:光纤" % self.id, self.sensor.optical, None)
        #         # cache.cache_save("中工创智:%s:传感器:温度" % self.id, self.sensor.temperature, None)
        #         # cache.cache_save("中工创智:%s:传感器:湿度" % self.id, self.sensor.humidity, None)
        #         #
        #         # cache.cache_save("中工创智:%s:计量:电压" % self.id, self.powerMeter.phaseA_voltage, None)
        #         # cache.cache_save("中工创智:%s:计量:电流" % self.id, self.powerMeter.phaseA_current, None)
        #         # cache.cache_save("中工创智:%s:计量:有功功率" % self.id, self.powerMeter.Power_active, None)
        #         # cache.cache_save("中工创智:%s:计量:无功功率" % self.id, self.powerMeter.Power_reactive, None)
        #         # cache.cache_save("中工创智:%s:计量:视在功率" % self.id, self.powerMeter.Power_total, None)
        #         # cache.cache_save("中工创智:%s:计量:功率因数" % self.id, self.powerMeter.Power_factor, None)
        #
        #         dev_msg = {
        #             "version":"1",
        #             "edgeTime":int(time.time()),
        #             "sensor":{
        #                 "temperature":self.sensor.temperature,
        #                 "humidity":self.sensor.humidity,
        #                 "optical":self.sensor.optical
        #             },
        #             "lamp":{
        #                 "red":self.lampStatus.red,
        #                 "green": self.lampStatus.green,
        #                 "yellow": self.lampStatus.yellow,
        #                 "beep": self.lampStatus.beep
        #             },
        #             "button":{
        #                 "green":self.buttonStatus.green,
        #                 "red":self.buttonStatus.red
        #             },
        #             "fan":self.fanStatus,
        #             "meters":{
        #                 "voltage":self.powerMeter.phaseA_voltage,
        #                 "current":self.powerMeter.phaseA_current,
        #                 "power":{
        #                     "total":self.powerMeter.Power_total,
        #                     "active":self.powerMeter.Power_active,
        #                     "reactive":self.powerMeter.Power_reactive,
        #                 },
        #                 "factor": self.powerMeter.Power_factor
        #             },
        #             "result":self.isFinished,
        #             "step":0,
        #             "index":self.lesson
        #         }
        #         # send to mqtt server
        #         self.interface.send_msg(json.dumps(dev_msg))
        #
            except Exception as e:
                try:
                    self.client.disconnect()
                except Exception as e:
                    logging.error(str(e))
                logging.error(str(e))
        t = Timer(self.collect_period, self.collect)
        t.start()

    def start(self):
        self.reconnect()
        self.collect()
