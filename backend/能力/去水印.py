# -*- coding: utf-8 -*-
"""去水印能力：去水印.json（RAIWRemoveVisibleWatermark）。"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 装填图片, 任务文件

工作流文件 = '去水印.json'


def 构建去水印(任务, comfy_url):
    if not 任务.输入图1:
        raise ValueError('去水印必须上传输入图1。')

    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)
    装填图片(api, 'LoadImage', str(任务文件(任务.输入图1)), 0, url=comfy_url)
    return api
