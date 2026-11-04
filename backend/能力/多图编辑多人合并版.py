# -*- coding: utf-8 -*-
"""多图编辑多人合并版能力：Qwen Edit 2509，社区Lora，双人合照 (2).json。

工作流要点（逐节点核对，改前先看这里）：
- 输入图 2~3 张柔性（2026-09-29 改）：图1（LoadImage 78）必填，进编码器 418 的 image1，
  是被保留的主体；图2（419）/ 图3（456）是要合进来的人，至少再传一张。
- 每个图位是一整套：LoadImage → 缩放（78/419/456 → 389/420/457）→ 该图位的 PreviewImage
  （394/455/458）+ 编码器 418 / 110 的 imageN。未传的图位把这三个节点整段摘掉。
  PreviewImage 是输出节点、images 是必需输入，只摘 LoadImage + 缩放会留下缺必需输入的非法节点
  → Comfy 校验 400，所以 PreviewImage 必须一起摘。编码器的 imageN 由 摘除节点 自动清掉。
- 提示词：正向写 418.prompt；负向 110.prompt 只在用户填写时覆盖（JSON 默认抑制词保留）。
- seed 有三处，缺一不可：KSampler 3（一采）、451（UltimateSDUpscaleNoUpscale 的放大重绘，
  class_type 不是 KSampler，必须单独写）、1111（SeedVR2 分块放大）。三处写同一个值。
  工作流自带的默认值（3/451=888888、1111=100）是固定值，不写就每次都一样，必须覆盖。
- 输出两张（docs/02 3.5）：SaveImage 452 = UltimateSDUpscale 成品（产物图片），
  SaveImage 1100 = SeedVR2 分块放大后（产物图片2）。原工作流有 3 个 SaveImage
  （60 一采原图 / 452 成品 / 454 拼接对比图），超过平台「一次最多 2 张图」会直接判失败，
  所以摘掉 60、454 及它的拼接链 453 / 459 / 424，和 rgthree 对比器 444。
  457 是图3 的缩放节点，图3 没传时和它一起摘，图3 有传时它同时喂给编码器，不能摘。
- 2026-09-29 工作流换版：新增 SeedVR2 分块放大链（1047 / 1048 / 1064 / 1073 / 1076 /
  1079 / 1089 / 1090 / 1095 / 1096 / 1098 / 1099 / 1109 / 1110 / 1111），末端
  SaveImage 1100 出放大图，输入取自 451。链上的 PreviewImage 1101 ~ 1103 落 Comfy
  temp、不计入产物，但它们是输出节点，不摘 Comfy 就会真跑这条链——本能力要这张放大图，
  所以照原样保留。
"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写参数, 上传到Comfy,
                            摘除节点, 任务文件, 随机种子)

工作流文件 = 'Qwen Edit 2509，社区Lora，双人合照 (2).json'

# 摘除：拼接对比图保存链 + 一采原图保存 + rgthree 对比器
摘除清单 = ('454', '453', '459', '424', '60', '444')

# 图位：LoadImage / 缩放 / 该图位 PreviewImage / 编码器输入名 / 任务列名（顺序即 图1→图3）
图位 = (
    ('78', '389', '394', 'image1', '输入图1'),
    ('419', '420', '455', 'image2', '输入图2'),
    ('456', '457', '458', 'image3', '输入图3'),
)

# 产物两个：452 成品（产物图片）、1100 SeedVR2 分块放大后（产物图片2）
放大后 = '1100'


def 构建多图编辑多人合并版(任务, comfy_url):
    # 2~3 张柔性：图1（主体）必填，图2/图3 至少再传一张（双人合照，最少两个人）
    已填 = [位 for 位 in 图位 if getattr(任务, 位[4])]
    if not 已填 or 已填[0][4] != '输入图1':
        raise ValueError('多图编辑多人合并版必须上传图1（主体）。')
    if len(已填) < 2:
        raise ValueError('多图编辑多人合并版至少要两张图：图1（主体）之外，图2/图3 至少再传一张。')

    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    # 装填：直接按节点 id 写，不依赖 LoadImage 在 JSON 里的出现顺序
    for 节点id, _缩放, _预览, _输入名, 列名 in 已填:
        文件 = str(任务文件(getattr(任务, 列名)))
        名字 = 上传到Comfy(comfy_url, 文件) if os.path.isfile(文件) else 文件
        写参数(api, 节点id, 'image', 名字)

    # 未传的图位整段摘掉：LoadImage + 缩放 + 该图位的 PreviewImage（理由见文件头）。
    # 编码器 418 / 110 的 imageN 由 摘除节点 自动清掉，不需要手工拆线。
    已填列名 = {位[4] for 位 in 已填}
    for 节点id, 缩放, 预览, _输入名, 列名 in 图位:
        if 列名 in 已填列名:
            continue
        for nid in (节点id, 缩放, 预览):
            摘除节点(api, nid)

    for nid in 摘除清单:
        摘除节点(api, nid)

    # 提示词：后端只 rstrip，不在后端拼接
    if 任务.正向提示词:
        写参数(api, '418', 'prompt', 任务.正向提示词.rstrip())
    if 任务.反向提示词:
        写参数(api, '110', 'prompt', 任务.反向提示词.rstrip())

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'KSampler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子
    api.setdefault('451', {}).setdefault('inputs', {})['seed'] = 种子
    # 1111 SeedVR2 也有 seed（工作流自带默认 100），不写就永远是 100
    for nid in 按类型找节点(api, 'SeedVR2VideoUpscaler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子

    # 两张图分别落前缀：提交并等待 按放大标记 _hd 分流到 产物图片 / 产物图片2
    写参数(api, '452', 'filename_prefix', 'aicg_edit2509')
    写参数(api, 放大后, 'filename_prefix', 'aicg_edit2509_hd')
    return api
