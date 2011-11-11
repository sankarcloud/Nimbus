#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from nimbus.graphics.models import resource, filter, filter_value, Data
from nimbus.shared import utils
import systeminfo


@resource
def disk_usage(manager, interactive):
    u"""Uso de disco"""
    diskinfo = systeminfo.DiskInfo("/")
    diskusage = diskinfo.get_used()
    return diskusage


@filter_value
def convert_data_to_gb(resource_name, data):
    if resource_name == "disk_usage":
        value = utils.filesizeformat(data.value, "GB")
        return Data(value, data.timestamp)
    else:
        return data


@filter_value
def datetime_to_str(resource_name, data):
    timestamp =  utils.datetime_to_str(data.timestamp)
    return Data(data.value, timestamp)


@filter
def duplicate_unary_list(resource_name, data_list):
    if len(data_list) == 1:
        return data_list * 2
    return data_list