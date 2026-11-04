# -*- coding: utf-8 -*-
"""参考生视频能力：H3-全能参考生视频（图9视频3音频3）.json。

节点（旧项目实测）：138 提示词(Input Text (Prompt)) / 图 137,139,141-147 /
视频 148-150 / 音频 151,155,156 / 132 时长 / 115 分辨率 / RandomNoise 种子。
平台硬上限 9 图 3 视频 3 音频，超出在提交侧已被 task 列限制；未提供的参考位柔性摘除。

参考视频的音轨：节点 136 的 ref_video_audios.ref_video_audio_N 接的是 VHS_LoadVideo
的第 3 个输出（音频），而 VHS 一旦被拉这个输出就会无条件去抽音频 —— 视频没有音轨时
ffmpeg 直接报 "Output file does not contain any stream"，整个任务失败。
ref_video_audios 本身是可选输入（min 0）且按「同序号」跟视频配对，所以这里逐个探测，
**没音轨的那条不接**，有音轨的照旧保留原声参考。
"""
import os
import subprocess

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写文本, 写参数,
                            写宽高比, 上传到Comfy, 摘除节点,
                            任务文件, 随机种子)

工作流文件 = 'H3-全能参考生视频（图9视频3音频3）.json'
图节点 = ['137', '139', '141', '142', '143', '144', '145', '146', '147']
视频节点 = ['148', '149', '150']
音频节点 = ['151', '155', '156']


def _有音轨(文件路径):
    """探测视频里有没有音频流。探不出来就返回 True（保持原行为，不引入新的失败模式）。

    本机 PATH 里既没有 ffmpeg 也没有 ffprobe（imageio-ffmpeg 只带 ffmpeg），
    所以跟 能力/音频剪辑.py 一个路子：跑 `ffmpeg -i`，从 stderr 里找 `Audio:` 行。
    """
    try:
        结果 = subprocess.run(
            [str(settings.FFMPEG_EXE), '-hide_banner', '-i', str(文件路径)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        文本 = 结果.stderr.decode('utf-8', 'ignore')
    except Exception:
        return True
    return any('Audio:' in 行 for 行 in 文本.splitlines())



def 构建参考生视频(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    写文本(api, 'Input Text (Prompt)', (任务.正向提示词 or '').rstrip())

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 10) if getattr(任务, '输入图%d' % i)]
    if not 图列表:
        raise ValueError('参考生视频至少要上传 1 张参考图。')
    for i, 相对路径 in enumerate(图列表[:9]):
        api[图节点[i]]['inputs']['image'] = 上传到Comfy(
            comfy_url, str(任务文件(相对路径)))
    for nid in 图节点[len(图列表):]:
        摘除节点(api, nid)

    视频列表 = [任务.输入视频1, 任务.输入视频2, 任务.输入视频3]
    视频列表 = [v for v in 视频列表 if v]
    for i, 相对路径 in enumerate(视频列表[:3]):
        api[视频节点[i]]['inputs']['video'] = 上传到Comfy(
            comfy_url, str(任务文件(相对路径)))
    for nid in 视频节点[len(视频列表):]:
        摘除节点(api, nid)

    # 没音轨的参考视频不接 ref_video_audio_N，否则 VHS_LoadVideo 抽音频必失败。
    # （用不到的参考位上面已经整节点摘除，悬空连线由 摘除节点 一并清掉了。）
    for nid in 按类型找节点(api, 'MiniMaxH3ReferenceToVideo'):
        节点输入 = api[nid].setdefault('inputs', {})
        for i, 相对路径 in enumerate(视频列表[:3]):
            if not _有音轨(任务文件(相对路径)):
                节点输入.pop('ref_video_audios.ref_video_audio_%d' % i, None)

    音频列表 = [任务.输入音频1, 任务.输入音频2, 任务.输入音频3]
    音频列表 = [a for a in 音频列表 if a]
    for i, 相对路径 in enumerate(音频列表[:3]):
        api[音频节点[i]]['inputs']['audio'] = 上传到Comfy(
            comfy_url, str(任务文件(相对路径)))
    for nid in 音频节点[len(音频列表):]:
        摘除节点(api, nid)

    # 视频时长：请求的视频生成秒数，写 PrimitiveFloat 时长节点（132）
    if 任务.视频时长 is not None:
        for nid in 按类型找节点(api, 'PrimitiveFloat'):
            api[nid].setdefault('inputs', {})['value'] = float(任务.视频时长)

    # 比例 + 一采MP 写 ResolutionSelector（115）；无视频长宽，宽高由分辨率节点算出
    if 任务.比例:
        写宽高比(api, 任务.比例,
                float(任务.一采MP) if 任务.一采MP is not None else None)

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'RandomNoise'):
        api[nid].setdefault('inputs', {})['noise_seed'] = 种子
    写参数(api, 'SaveVideo', 'filename_prefix', 'video/aicg_ref2v')
    return api
