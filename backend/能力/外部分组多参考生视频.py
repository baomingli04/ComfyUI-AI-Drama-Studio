# -*- coding: utf-8 -*-
"""外部分组多参考生视频能力：外部分组多参考生视频_导演台.json（r2v + 外部分组，r2v_groups）。

同 D8 的外部分组机制，但走 r2v_groups：4 个
MiniMaxH3DirectorGroupReferenceToVideo（37 / 38 / 39 / 42）经
GroupsCombine（32）灌进 Director.r2v_groups。

参考素材走 LoadImage（18 / 19 / 20 / 40 / 41）和 VHS_LoadVideo（45），
不是 Director 的 refs —— 所以要把上传后的文件名直接写进这些节点：
组1 = 图1+图2，组2 = 图3，组3 = 图4+图5，组4 = 参考视频。

每组提示词 / 每组时长用 task 上的 组1~4提示词 / 组1~4时长（docs/02 第 9 节）：
为空则回落到页面填的 正向提示词 / 视频时长。所以页面不填组参数时，4 个组会被
同一份公共提示词 + 公共时长覆盖，工作流里各组自带的 prompt / duration_sec
（组1 是 <Subject N> 六段式、组2 带 <Audio 1>、组3/组4 是 15 秒）都不保留。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数, 取组参数

工作流文件 = '外部分组多参考生视频_导演台.json'

# 页上 输入图1..5 / 输入视频1 → 工作流里的 LoadImage / VHS_LoadVideo 节点
图位表 = ('18', '19', '20', '40', '41')
视频位 = '45'
组表 = ('37', '38', '39', '42')


def 构建外部分组多参考生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 6)]
    if not all(图列表):
        raise ValueError('外部分组多参考生视频需要 5 张参考图（组1两张、组2一张、组3两张）。')
    if not 任务.输入视频1:
        raise ValueError('外部分组多参考生视频还需要 1 个参考视频（组4）。')

    上传名 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 图列表]
    for 节点, 文件名 in zip(图位表, 上传名):
        api[节点].setdefault('inputs', {})['image'] = 文件名

    视频名 = 上传到Comfy(comfy_url, str(任务文件(任务.输入视频1)))
    api[视频位].setdefault('inputs', {})['video'] = 视频名

    组参数 = 取组参数(任务, len(组表))
    for 组, (提示词, 时长) in zip(组表, 组参数):
        组输入 = api[组].setdefault('inputs', {})
        if 提示词:
            组输入['prompt'] = 提示词
        if 时长:
            组输入['duration_sec'] = 时长

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
    )
    return api
