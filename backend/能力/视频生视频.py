# -*- coding: utf-8 -*-
"""视频生视频能力：视频生视频_导演台.json（v2v — 视频转视频）。

Director 节点 5，timelineMode=video：源视频文件名写进 timeline_data.video.videoFile，
源片每一段自动作为 <Video 1>。v2v 没有参考图槽，要挂参考图请用「参考视频生视频」。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数

工作流文件 = '视频生视频_导演台.json'


def 构建视频生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    if not 任务.输入视频1:
        raise ValueError('视频生视频必须上传 1 个源视频。')
    源视频 = 上传到Comfy(comfy_url, str(任务文件(任务.输入视频1)))

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
        源视频=源视频,
    )
    return api
