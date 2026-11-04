# -*- coding: utf-8 -*-
"""二采重绘能力：Minimax_H3二采重绘.json（源视频二次采样重绘/超分）。

节点（旧项目实测）：138 提示词 / 144 源视频 / 137,139,146-151 参考图 /
155,163,164 参考音频 / 115 一采分辨率 / 214 二采分辨率 / 168 真输出。
一采MP / 二采MP 分别写 task 对应列。
「一采 / 二采」是**同一次运行内的两级采样**（115 一采 → 302 → 214 二采），
源视频是用户上传的素材（144 VHS_LoadVideo），不是任何一采产物。

参考图 / 参考音频 / 源视频**三者都是可选的**（旧项目 `Minimax_H3二采重绘.py` 口径一致）：
图 0~8 张、音频 0~3 个、源视频 0~1 个，传几个接几个，未用的槽位整体柔性摘除。
源视频没传时整条视频分支 144→309→159→297 级联摘除（只摘 144 会让 309 的 required
输入 image 缺失 → 校验失败），302 的 ref_videos / ref_video_audios 本就是可选输入。

源视频的音轨：节点 302 的 ref_video_audios.ref_video_audio_0 接的是 VHS_LoadVideo
的第 3 个输出（音频），而 VHS 一旦被拉这个输出就会去抽音频 —— 视频没有音轨时
ffmpeg 直接报 "Output file does not contain any stream"，整个任务失败。
（工作流里 144[2] 的另一个消费方 297 CreateVideo 是悬空节点，ComfyUI 只执行从
输出节点可达的部分，它会被裁掉，所以摘掉 302 这条连线就够。）
ref_video_audios 是可选输入（min 0），所以这里探测一次，**没音轨就不接**。
"""
import os
import subprocess

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写文本, 写参数,
                            上传到Comfy, 摘除节点, 写宽高比,
                            任务文件, 随机种子)

工作流文件 = 'Minimax_H3二采重绘，秒变清晰+超高一致性，效率起飞！.json'
提示词节点 = '138'
源视频节点 = '144'
# 视频分支整条链路：144 VHS_LoadVideo → 309 ImageResizeKJv2 → 159 easy clearCacheAll
#                   → 297 CreateVideo（末端死节点，输出无人消费）
# 没传源视频时必须整条级联摘除（理由见 构建二采重绘 里的注释）。
视频分支 = ['144', '309', '159', '297']
图节点 = ['137', '139', '146', '147', '148', '149', '150', '151']
# 参考图槽位：LoadImage 与 Resize 中间件一一对应，摘除必须成对摘，
# 否则 302.ref_image_x 指向失去输入的 Resize → 整条视频输出链校验失败。
图中间件 = ['198', '234', '235', '236', '237', '238', '239', '240']
音频节点 = ['155', '163', '164']
音频中间件 = ['303', '304', '305']
一采节点 = '115'
二采节点 = '214'
输出节点 = '168'


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


def 构建二采重绘(任务, comfy_url):
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    写文本(api, 提示词节点, (任务.正向提示词 or '').rstrip())

    # 源视频可选（0~1）。没传就整条视频分支级联摘除：
    #   144 VHS_LoadVideo → 309 ImageResizeKJv2 → 159 easy clearCacheAll → 297 CreateVideo
    # 只摘 144 不行 —— 309.image 是 required 输入，摘掉 144 后 309 会变成
    # 「必填输入缺失」的活节点（159 还被 302.ref_videos 引用）→ 校验失败。
    # 302 的 ref_videos / ref_video_audios 都是可选输入，整条摘干净照样能生成。
    # （297 是从输出节点不可达的死叶，ComfyUI 本来就不执行它，一并摘掉省事。）
    if 任务.输入视频1:
        api[源视频节点]['inputs']['video'] = 上传到Comfy(
            comfy_url, str(任务文件(任务.输入视频1)))

        # 源视频没音轨就不接 ref_video_audio_0，否则 VHS_LoadVideo 抽音频必失败。
        if not _有音轨(任务文件(任务.输入视频1)):
            for nid in 按类型找节点(api, 'MiniMaxH3ReferenceToVideo'):
                api[nid].setdefault('inputs', {}).pop(
                    'ref_video_audios.ref_video_audio_0', None)
    else:
        for nid in 视频分支:
            摘除节点(api, nid)

    图列表 = [getattr(任务, '输入图%d' % i) for i in range(1, 10) if getattr(任务, '输入图%d' % i)]
    for i, 相对路径 in enumerate(图列表[:len(图节点)]):
        api[图节点[i]]['inputs']['image'] = 上传到Comfy(
            comfy_url, str(任务文件(相对路径)))
    for i in range(len(图列表), len(图节点)):
        摘除节点(api, 图节点[i])
        摘除节点(api, 图中间件[i])

    音频列表 = [任务.输入音频1, 任务.输入音频2, 任务.输入音频3]
    音频列表 = [a for a in 音频列表 if a]
    for i, 相对路径 in enumerate(音频列表[:3]):
        api[音频节点[i]]['inputs']['audio'] = 上传到Comfy(
            comfy_url, str(任务文件(相对路径)))
    for i in range(len(音频列表), len(音频节点)):
        摘除节点(api, 音频节点[i])
        摘除节点(api, 音频中间件[i])

    # 比例 + MP 写两个 ResolutionSelector（115 一采 / 214 二采）
    # 前端已按同一公式（比例 + 一采MP → 32 倍数）算出宽高并只读显示，这里只传「比例 + MP」
    if 任务.比例:
        写宽高比(api, 任务.比例,
                float(任务.一采MP) if 任务.一采MP is not None else None,
                节点id=一采节点)
        写宽高比(api, 任务.比例,
                float(任务.二采MP) if 任务.二采MP is not None else None,
                节点id=二采节点)
    else:
        # 没选比例时只写 MP（保持旧行为）
        if 任务.一采MP is not None:
            api[一采节点].setdefault('inputs', {})['megapixels'] = float(任务.一采MP)
        if 任务.二采MP is not None:
            api[二采节点].setdefault('inputs', {})['megapixels'] = float(任务.二采MP)

    # 视频时长：请求的视频生成秒数，写 PrimitiveFloat 时长节点（132）
    if 任务.视频时长 is not None:
        for nid in 按类型找节点(api, 'PrimitiveFloat'):
            api[nid].setdefault('inputs', {})['value'] = float(任务.视频时长)

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'RandomNoise'):
        api[nid].setdefault('inputs', {})['noise_seed'] = 种子
    写参数(api, 输出节点, 'filename_prefix', 'video/aicg_erchai')
    return api
