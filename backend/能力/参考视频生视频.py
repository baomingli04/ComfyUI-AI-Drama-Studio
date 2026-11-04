# -*- coding: utf-8 -*-
"""参考视频生视频能力：参考视频生视频_导演台.json（rv2v — 参考素材改视频）。

Director 节点 5，timelineMode=video：源视频 + 参考图 1–9（+参考音频 1–3）。
源片自动作为 <Video 1>，参考图用 <Picture N> 引用，参考音频用 <Audio J>。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数

工作流文件 = '参考视频生视频_导演台.json'


def 构建参考视频生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    if not 任务.输入视频1:
        raise ValueError('参考视频生视频必须上传 1 个源视频。')
    源视频 = 上传到Comfy(comfy_url, str(任务文件(任务.输入视频1)))

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 10)]
    图列表 = [p for p in 图列表 if p]
    参考图 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 图列表[:9]]

    # 参考视频（global.refVideos，docs/13 §0.5）。输入视频1 已被源视频占用，
    # 所以参考视频只剩 输入视频2 / 输入视频3 两个位（官方上限 3，这里实际 2）。
    参考视频列表 = [p for p in [任务.输入视频2, 任务.输入视频3] if p]
    参考视频 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 参考视频列表[:2]]

    音频列表 = [p for p in [任务.输入音频1, 任务.输入音频2, 任务.输入音频3] if p]
    参考音频 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 音频列表[:3]]

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
        参考图=参考图,
        参考视频=参考视频,
        参考音频=参考音频,
    )
    return api
