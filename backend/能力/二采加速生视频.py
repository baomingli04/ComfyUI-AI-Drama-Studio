# -*- coding: utf-8 -*-
"""二采加速生视频能力：二采加速_导演台.json（r2v 一采 + 二采精修/放大）。

结构：Director 节点 12 跑一采（r2v，同「加速版」那条线），产物走 CreateVideo 6 → SaveVideo 7；
二采由 MiniMaxH3DirectorRefine 节点 38 描述，经 Director.refine 口回灌，
产物走 CreateVideo 19 → SaveVideo 20。所以一次任务会出两个 mp4（一采 / 二采）。

task 上没有给「二采模式 / 采样器 / 次数」单独开列（docs/02 只定了一采MP、二采MP、比例），
所以这几项目前沿用工作流默认值；页上能改的是：一采画布（视频宽/视频高）、
二采目标比例（比例）、二采档位（二采MP），以及常规导演参数。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数

工作流文件 = '二采加速_导演台.json'
精修节点 = '38'

# 页上传的是短标签（16:9），节点要完整标签（16:9 (宽屏)）
比例标签 = {
    '1:1': '1:1 (方形)',
    '2:3': '2:3 (竖版照片)',
    '3:2': '3:2 (横版照片)',
    '3:4': '3:4 (竖版标准)',
    '4:3': '4:3 (标准)',
    '9:16': '9:16 (竖屏)',
    '16:9': '16:9 (宽屏)',
    '21:9': '21:9 (超宽)',
    '跟随导演台': '跟随导演台',
    '自定义': '自定义',
}


def 填二采(api, 比例=None, 二采MP=None):
    """只改 MiniMaxH3DirectorRefine 节点的放大目标，其余沿用工作流默认。"""
    节点 = api.get(精修节点)
    if not isinstance(节点, dict):
        return api
    inputs = 节点.setdefault('inputs', {})
    if 比例:
        inputs['aspect_ratio'] = 比例标签.get(str(比例).strip(), str(比例).strip())
    if 二采MP is not None:
        inputs['megapixels'] = float(二采MP)
    return api


def 构建二采加速生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 10)]
    图列表 = [p for p in 图列表 if p]
    if not 图列表:
        raise ValueError('二采加速生视频至少要上传 1 张参考图。')

    参考图 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 图列表[:9]]

    视频列表 = [p for p in [任务.输入视频1, 任务.输入视频2, 任务.输入视频3] if p]
    参考视频 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 视频列表[:3]]

    音频列表 = [p for p in [任务.输入音频1, 任务.输入音频2, 任务.输入音频3] if p]
    参考音频 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 音频列表[:3]]

    填导演参数(
        api,
        提示词=(任务.正向提示词 or '').rstrip(),
        反向提示词=任务.反向提示词 if 任务.反向提示词 else None,
        seed=任务.seed,
        cfg=float(任务.cfg) if 任务.cfg is not None else None,
        宽=任务.视频宽,
        高=任务.视频高,
        兆像素=float(任务.一采MP) if 任务.一采MP is not None else None,
        比例=任务.比例,
        时长秒=任务.视频时长,
        参考图=参考图,
        参考视频=参考视频,
        参考音频=参考音频,
    )
    填二采(api, 比例=任务.比例, 二采MP=任务.二采MP)
    return api
