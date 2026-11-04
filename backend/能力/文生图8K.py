# -*- coding: utf-8 -*-
"""文生图8K能力：Z-Image文生图8K.json。提示词原样透传，禁止拼接。

出两张：
  1x  = VAE 解码后的原尺寸图，等于前端填的图片宽×图片高（节点 179）
  4x  = 原尺寸 ×4 后过 TTP 分块 + SeedVR2 超分拼回的大图（节点 160）
前端填的宽高是「正常尺寸」（1x 那张），4 倍是工作流默认（节点 178 倍数=4），不在页面上暴露。

2026-09-29 工作流换版：新版把原来 1x 的 SaveImage（节点 179）删了，1x 路径只剩
PreviewImage 177（落 Comfy temp，不计入产物）。按 docs/02 3.5 口径（产物图片=1x、
产物图片2=4x，两张仅本能力出），改由后端装载后补一个 SaveImage 接 VAE 解码输出，
节点 id 仍用 179。其余节点 id 与参数与旧版逐项一致（仅 SeedVR2 的 DiT 模型换成
seedvr2_ema_3b_fp16，本模块不写模型名）。
"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写文本,
                            写参数, 任务文件, 随机种子)

工作流文件 = 'Z-Image文生图8K.json'

# 节点定位：8K 工作流没有【正向/反向提示词】标题，按节点 id 直接写
正向节点 = '163'          # Text Multiline（多行文本）→ 121 CLIPTextEncode
反向节点 = '7'            # CLIPTextEncode（空文本，cfg=1 下基本不生效，保留可写）
画布节点类 = 'EmptyLatentImage'   # 54：1x 尺寸就写在这里
倍数节点 = '178'          # PrimitiveFloat：放大倍数，默认 4
保存1x = '179'            # SaveImage：接 VAE 解码，出原尺寸图（新版工作流已删，由下面补回）
保存4x = '160'            # SaveImage：接 TTP 拼接，出 4 倍大图


def 补1x保存节点(api):
    """新版工作流没有 1x 的 SaveImage 时，补一个接 VAE 解码输出的保存节点。

    节点 id 用 179（与旧版一致）。已有 179、或已有别的 SaveImage 接同一路输出时不重复补。
    """
    if 保存1x in api:
        return
    解码 = 按类型找节点(api, 'VAEDecode')
    if not 解码:
        return
    目标 = [解码[0], 0]
    for 节点 in api.values():
        if 节点.get('class_type') == 'SaveImage' and 节点.get('inputs', {}).get('images') == 目标:
            return
    api[保存1x] = {
        'inputs': {'images': 目标, 'filename_prefix': 'aicg_zimage'},
        'class_type': 'SaveImage',
        '_meta': {'title': '保存图像1x'},
    }


def 构建文生图8K(任务, comfy_url):
    """按 task 内容装填文生图8K工作流，返回 API 格式 dict。"""
    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    补1x保存节点(api)

    写文本(api, 正向节点, (任务.正向提示词 or '').rstrip())
    if 任务.反向提示词:
        写文本(api, 反向节点, 任务.反向提示词.rstrip())

    # 尺寸：前端填的是 1x 尺寸，写到空 Latent；不填则沿用工作流默认
    if 任务.图片宽 or 任务.图片高:
        ids = 按类型找节点(api, 画布节点类)
        if ids:
            inputs = api[ids[0]].setdefault('inputs', {})
            inputs['width'] = 任务.图片宽 or inputs.get('width', 1080)
            inputs['height'] = 任务.图片高 or inputs.get('height', 1920)

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'KSampler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子
    # 135 SeedVR2 也有 seed（工作流自带默认 2794489657），不写就永远是那个固定值
    for nid in 按类型找节点(api, 'SeedVR2VideoUpscaler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子

    # 两张图分别落前缀：提交并等待 按前缀 _4x 分流到 产物图片 / 产物图片2
    写参数(api, 保存1x, 'filename_prefix', 'aicg_zimage')
    写参数(api, 保存4x, 'filename_prefix', 'aicg_zimage_4x')
    return api
