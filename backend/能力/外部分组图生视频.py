# -*- coding: utf-8 -*-
"""外部分组图生视频能力：外部分组图生视频_导演台.json（fl2v + 外部分组，i2v_groups）。

和前面几条不一样：真正出片的不是 Director 自己的时间线，而是从
MiniMaxH3DirectorGroupsCombine（节点 32）灌进 Director.i2v_groups 的 4 个
MiniMaxH3DirectorGroupImageToVideo 组（节点 23 / 24 / 31 / 35）。
组在 execute time 覆盖时间线（external-priority），所以段的 prompt、时长由组决定。

组里的图走 LoadImage 节点（18 / 19 / 20 / 30），不是 Director 的 refs，
所以要把上传后的文件名直接写进 LoadImage 的 image。

每组提示词 / 每组时长用 task 上的 组1~4提示词 / 组1~4时长（docs/02 第 9 节）：
为空则回落到页面填的 正向提示词 / 视频时长（节点侧本来就是这个 fallback，两边
保持一致）。所以页面不填组参数时，4 个组会被同一份公共提示词 + 公共时长覆盖，
工作流里各组自带的 prompt / duration_sec 不保留。
每组首/尾帧沿用工作流既有的 4 个图位。
"""
import os

from django.conf import settings

from 能力.工作流工具 import 装载工作流, 上传到Comfy, 任务文件
from 能力.导演台工具 import 填导演参数, 取组参数

工作流文件 = '外部分组图生视频_导演台.json'

# 组节点 id → （首帧 LoadImage 节点, 尾帧 LoadImage 节点）；None 表示这组没有这个口
# 顺序必须和 GroupsCombine 的 group_0..group_3 一致（23 / 24 / 35 / 31），
# 也就是出片的段序：组1(首尾) → 组2(首) → 组3(尾) → 组4(纯提示词)。
# 写反了页上的「组3 / 组4」会对调。
组表 = (
    ('23', '18', '19'),
    ('24', '20', None),
    ('35', None, '30'),
    ('31', None, None),
)
# 页上 输入图1..4 依次对应 组1首 / 组1尾 / 组2首 / 组3尾。
# 注意节点 30 是节点 35 的 last_frame，而 35 是 GroupsCombine 的 group_2
# = 出片顺序里的第 3 组；第 4 组是节点 31，纯提示词、不带图。
图位表 = ('18', '19', '20', '30')


def 构建外部分组图生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 5)]
    if not all(图列表):
        raise ValueError('外部分组图生视频需要 4 张图：组1首帧、组1尾帧、组2首帧、组4尾帧。')

    上传名 = [上传到Comfy(comfy_url, str(任务文件(p))) for p in 图列表]
    for 节点, 文件名 in zip(图位表, 上传名):
        api[节点].setdefault('inputs', {})['image'] = 文件名

    组参数 = 取组参数(任务, len(组表))
    for (组, _首, _尾), (提示词, 时长) in zip(组表, 组参数):
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
