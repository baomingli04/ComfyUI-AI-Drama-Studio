# -*- coding: utf-8 -*-
"""首尾帧生视频能力：首尾帧生视频_导演台.json（fl2v — 首尾帧生视频）。

Director 节点 5，走的是独立的 fl2v 时间线（timelineMode=fl2v），结构跟 t2v/r2v
不一样：素材不在 segments 里，而是 shots[] 的 startImage / endImage。
- 只传首帧 = 图生视频；只传尾帧 或 首+尾 = 首尾帧过渡；都不传 = fl2va 上的文生。
- 每组的帧数由 durationSec 决定（同样按 17k+5 对齐）。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数, 做首尾镜头

工作流文件 = '首尾帧生视频_导演台.json'


def 构建首尾帧生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    首帧 = 上传到Comfy(comfy_url, str(任务文件(任务.输入图1))) if 任务.输入图1 else None
    尾帧 = 上传到Comfy(comfy_url, str(任务文件(任务.输入图2))) if 任务.输入图2 else None

    镜头 = 做首尾镜头(
        首帧文件=首帧,
        尾帧文件=尾帧,
        时长秒=float(任务.视频时长 or 5),
        提示词=(任务.正向提示词 or '').rstrip(),
        反向提示词=(任务.反向提示词 or '').strip(),
    )

    # 自定义档（docs/13 §0.6 第 1 层：output.aspectRatio=自定义，不走公式）
    # → 直接把前端按「比例 + 一采MP」算好并回填的 视频宽/视频高 传进去，不传 比例 + MP。
    填导演参数(
        api,
        提示词=(任务.正向提示词 or '').rstrip(),
        反向提示词=任务.反向提示词 if 任务.反向提示词 else None,
        seed=任务.seed,
        cfg=float(任务.cfg) if 任务.cfg is not None else None,
        宽=任务.视频宽,
        高=任务.视频高,
        时长秒=任务.视频时长,
        镜头=镜头,
    )
    return api
