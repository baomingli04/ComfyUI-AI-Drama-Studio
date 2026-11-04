# -*- coding: utf-8 -*-
"""人物替换能力：MiniMax-H3人物场景替换.json。

节点（旧项目实测）：138 提示词 / 195 参考图 / 184 参考视频 / 223 参考音频 /
132 生成秒数(PrimitiveFloat) / 115 分辨率(ResolutionSelector) / 190,191 输出帧率。
未提供的参考位柔性摘除，绝不能留空 COMBO 路径（会被校验拒绝）。
"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写文本, 写参数,
                            写宽高比, 宽高算比例, 上传到Comfy, 摘除节点,
                            任务文件, 随机种子, _输入名)

工作流文件 = 'MiniMax-H3人物场景替换.json'
节点 = {'提示词': '138', '图': '195', '视频': '184', '音频': '223',
        '秒数': '132', '分辨率': '115', '输出帧率': ('190', '191')}


def 构建人物替换(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    写文本(api, 节点['提示词'], (任务.正向提示词 or '').rstrip())

    # 参考图（必填：人物替换的底图）
    if not 任务.输入图1:
        raise ValueError('人物替换必须上传输入图1。')
    api[节点['图']]['inputs']['image'] = 上传到Comfy(
        comfy_url, str(任务文件(任务.输入图1)))

    # 参考视频 / 参考音频：可选
    if 任务.输入视频1:
        api[节点['视频']]['inputs']['video'] = 上传到Comfy(
            comfy_url, str(任务文件(任务.输入视频1)))
    else:
        摘除节点(api, 节点['视频'])
    if 任务.输入音频1:
        api[节点['音频']]['inputs']['audio'] = 上传到Comfy(
            comfy_url, str(任务文件(任务.输入音频1)))
    else:
        摘除节点(api, 节点['音频'])

    # 生成秒数：无独立列，固定 5 秒（有视频跟随视频时长的能力后端不做解析，见 08 待办）
    api[节点['秒数']].setdefault('inputs', {})['value'] = 5.0

    # 分辨率：视频宽/高 → 比例标签 + 兆像素
    if 任务.视频宽 and 任务.视频高:
        写宽高比(api, 宽高算比例(任务.视频宽, 任务.视频高),
                任务.视频宽 * 任务.视频高 / 1000000.0, 节点id=节点['分辨率'])

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'RandomNoise'):
        api[nid].setdefault('inputs', {})['noise_seed'] = 种子
    return api
