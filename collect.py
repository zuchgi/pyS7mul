#!/usr/bin/python
# -*- coding: UTF-8 -*-
import logging
import devinfo
import idesk

logging.basicConfig(level=logging.ERROR)
device = []


def is_dev_config_ok(dev):
    try:
        if dev['index'] is None \
                or dev['ip'] is None \
                or dev['rack'] is None \
                or dev['slot'] is None:
            return False
        else:
            return True
    except Exception as e:
        logging.error(str(e))
        return False


def dev_install():
    # 获取设备配置信息
    _dev_array = devinfo.get_dev_config()
    for _dev in _dev_array:
        if is_dev_config_ok(_dev):
            device.append(idesk.iDesk(_dev['ip'],
                                      _dev['rack'],
                                      _dev['slot'],
                                      devinfo.get_time_config()['reconnect'],
                                      devinfo.get_time_config()['telemetry'],
                                      _dev['index']))
            logging.info("dev : %s installed !" + str(_dev['index']))
            device[-1].start()
