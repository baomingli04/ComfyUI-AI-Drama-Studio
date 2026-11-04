# -*- coding: utf-8 -*-
"""动漫转真人能力：动漫转真人_直接放大.json（Qwen 动漫转写实 + SeedVR2 放大）。

工作流要点（逐节点核对，改前先看这里）：
- 单张输入图：LoadImage 78 → 243（ImageScaleToTotalPixels，megapixels=1）→ 110 编码
  → 88 VAEEncode → KSampler 3 → 8 VAEDecode → 337/338 卸载模型 → 293 SeedVR2 放大
  → 295 SaveImage。全程只有一个 SaveImage，产物 1 张图，不用摘节点。
- 提示词：正向写 110.prompt；负向 77.prompt 只在用户填写时覆盖。
- seed 两处，缺一不可：KSampler 3（一采）+ 293（SeedVR2 放大）。两处写同一个值。
  工作流自带的默认值（3=640173704223966、293=1837124755）是固定值，不写就每次都一样，必须覆盖。
- 293 的 resolution=2048 / max_resolution=3800 / batch_size=5 是工作流自带值，
  本次不动；这条很吃显存和时间，实测要调再说。
- 2026-09-29 工作流换版：节点 id 与参数全部保留，只多了 4 对 SetNode / GetNode
  （model / clip / vae / ref_img1）做连线中转，语义不变，本模块逻辑无需改；
  SeedVR2 的 DiT 模型换成 seedvr2_ema_3b_fp16（本模块不写模型名，不受影响）。
"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写参数, 装填图片,
                            任务文件, 随机种子)

工作流文件 = '动漫转真人_直接放大.json'


def 构建动漫转真人(任务, comfy_url):
    if not 任务.输入图1:
        raise ValueError('动漫转真人必须上传输入图1。')

    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    装填图片(api, 'LoadImage', str(任务文件(任务.输入图1)), 0, url=comfy_url)

    # 提示词：后端只 rstrip，不在后端拼接
    if 任务.正向提示词:
        写参数(api, '110', 'prompt', 任务.正向提示词.rstrip())
    if 任务.反向提示词:
        写参数(api, '77', 'prompt', 任务.反向提示词.rstrip())

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'KSampler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子
    # 293 SeedVR2 也有 seed（工作流自带默认 1837124755），不写就永远是那个固定值
    for nid in 按类型找节点(api, 'SeedVR2VideoUpscaler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子
    写参数(api, '295', 'filename_prefix', 'aicg_anime2real')
    return api
