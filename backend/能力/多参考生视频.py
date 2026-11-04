# -*- coding: utf-8 -*-
"""多参考生视频能力：多参考生视频_导演台.json（r2v — 参考主体生视频）。

Director 节点 5。页上填：正向/反向提示词、seed、cfg、宽、高、时长（秒），
外加参考图 1–9 / 参考视频 1–3 / 参考音频 1–3。
参考素材要先传到 ComfyUI input，再把文件名写进 timeline_data 的段 refs；
提示词里用 <Picture 1> / <Video 1> / <Audio 1> 引用，编号 = 上传顺序。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数

工作流文件 = '多参考生视频_导演台.json'


def 构建多参考生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 10)]
    图列表 = [p for p in 图列表 if p]
    if not 图列表:
        raise ValueError('多参考生视频至少要上传 1 张参考图。')

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
    return api
