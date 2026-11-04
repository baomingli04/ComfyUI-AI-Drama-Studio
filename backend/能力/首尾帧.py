# -*- coding: utf-8 -*-
"""首尾帧能力：H3-首尾帧8步加速.json。

节点（旧项目实测）：LoadImage 首帧 idx0 / 尾帧 idx1，
提示词写 MiniMaxH3AudioConditioningT8.prompt，种子写 RandomNoise.noise_seed。
画布与时长也落在 MiniMaxH3AudioConditioningT8（节点 6）上：width / height / length。
这个工作流**不认 MP**：页上的「比例 + 一采MP」只是前端用来算宽高的输入，
传过来的只有像素宽高 + 时长，所以这里只写宽高和帧数，不写 MP。
"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写参数,
                            装填图片, 任务文件, 随机种子)
from 能力.导演台工具 import 最小帧数

工作流文件 = 'H3-首尾帧8步加速.json'


def 构建首尾帧(任务, comfy_url):
    if not 任务.输入图1:
        raise ValueError('首尾帧生视频至少要上传首帧（输入图1）。')

    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    装填图片(api, 'LoadImage', str(任务文件(任务.输入图1)), 0, url=comfy_url)
    if 任务.输入图2:
        装填图片(api, 'LoadImage', str(任务文件(任务.输入图2)), 1, url=comfy_url)
    else:
        # 只有首帧也允许（工作流默认尾帧沿用 JSON 内置），不摘除避免断链
        pass

    if 任务.正向提示词:
        ids = 按类型找节点(api, 'MiniMaxH3AudioConditioningT8')
        if ids:
            api[ids[0]].setdefault('inputs', {})['prompt'] = 任务.正向提示词.rstrip()

    # 画布与帧数：节点 6 的 width / height / length。
    # length 是**帧数**不是秒，按 MiniMax 的 17k+5 规则换算（24fps，与工作流
    # VHS_VideoCombine.frame_rate 一致，5 秒 = 124 帧，和 JSON 自带默认对得上）。
    画布ids = 按类型找节点(api, 'MiniMaxH3AudioConditioningT8')
    if 画布ids:
        画布 = api[画布ids[0]].setdefault('inputs', {})
        if 任务.视频宽:
            画布['width'] = int(任务.视频宽)
        if 任务.视频高:
            画布['height'] = int(任务.视频高)
        if 任务.视频时长:
            画布['length'] = 最小帧数(任务.视频时长)

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'RandomNoise'):
        api[nid].setdefault('inputs', {})['noise_seed'] = 种子
    写参数(api, 'VHS_VideoCombine', 'filename_prefix', 'aicg_fl')
    return api
