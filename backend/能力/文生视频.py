# -*- coding: utf-8 -*-
"""文生视频能力：文生视频_导演台.json（t2v — 文生视频）。

Director 节点 5。页上填：正向/反向提示词、seed、cfg、宽、高、时长（秒）。

帧率不传，沿用工作流默认的 24（用户要求「帧率要用每个工作流默认写的」）。
总帧数 = 最小帧数(时长, 帧率)，即 17k+5，不另存列。

timeline 走 build_gen_director_plan（prompt_batch → 强制 segment）。
本工作流不接受任何媒体，参考图/视频/音频一律为空。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流
from 能力.导演台工具 import 填导演参数

工作流文件 = '文生视频_导演台.json'


def 构建文生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

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
    )
    return api
