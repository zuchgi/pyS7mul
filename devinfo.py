#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json

# 获取用户设置
setting = json.load(open("./config.json", encoding='utf-8'))


def get_dev_config():
    return setting['dev']


def get_time_config():
    return setting['time']


def get_server_config():
    return setting['server']
