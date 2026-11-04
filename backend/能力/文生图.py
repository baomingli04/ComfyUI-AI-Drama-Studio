# -*- coding: utf-8 -*-
"""文生图能力：纯文生图_Z-Image.json。提示词原样透传，禁止拼接。"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按标题找节点, 按类型找节点, 写文本,
                            写参数, 任务文件, 随机种子)

工作流文件 = '纯文生图_Z-Image.json'
正向标题 = '【正向提示词】在这里输入'
反向标题 = '【反向提示词】在这里输入'


def 构建文生图(任务, comfy_url):
    """按 task 内容装填文生图工作流，返回 API 格式 dict。"""
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    写文本(api, 正向标题, (任务.正向提示词 or '').rstrip())
    if 任务.反向提示词:
        写文本(api, 反向标题, 任务.反向提示词.rstrip())

    # 尺寸：传了才覆盖，否则沿用工作流默认
    if 任务.图片宽 or 任务.图片高:
        ids = 按类型找节点(api, 'SDXLEmptyLatentSizePicker+')
        if ids:
            inputs = api[ids[0]].setdefault('inputs', {})
            inputs['width_override'] = 任务.图片宽 or inputs.get('width_override', 512)
            inputs['height_override'] = 任务.图片高 or inputs.get('height_override', 896)

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'KSampler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子
    写参数(api, 'SaveImage', 'filename_prefix', 'aicg_zimage')
    return api
