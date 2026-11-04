# -*- coding: utf-8 -*-
"""三图编辑一致版能力：Qwen Edit 2511 双图编辑【一致性加强版】电商_摄影等 (3).json。

工作流要点（逐节点核对，改前先看这里）：
- 三张输入图：LoadImage 13（主图）/ 12 / 32，各自经一个 QwenEditConfigPreparer
  串成 refs 链 15 → 14 → 34；末端 TextEncodeQwenImageEditPlusCustom 节点 10 只有
  configs 一个口，吃链尾（inputs['configs']）。
- 主图是节点 13（QwenEditConfigPreparer 15 的 ref_main_image=true、ref_crop=pad、
  长边 2300），所以页面第 1 个上传位给主图，不是按 LoadImage 数字顺序装填。
- 1~3 张柔性（2026-09-29）：图1（主图）必填，图2/图3 可选，允许跳着传（如只传图1+图3）。
  没传的图位整支摘除（Preparer + QwenEditAdaptiveLongestEdge + LoadImage），
  再把 refs 链重接到剩下的链尾。
  ⚠️ 摘除必须排在接链之前：工作流工具.摘除节点() 除了 pop 节点，还会把指向它的
  输入键一并删掉，反过来做会把刚写好的 configs 删没，节点 10 直接缺输入。
- 提示词落在 PrimitiveStringMultiline 节点 8 的 value；节点 10 的 instruction 是
  工作流固定的英文改写指令，不能覆盖。
- 输出两张（docs/02 3.5）：SaveImage 22 = 2511 成品（产物图片），
  SaveImage 1100 = SeedVR2 分块放大后（产物图片2）。SaveImage 25 是「三张输入 + 结果」
  的拼接对比图，连带它的拼接链 24 / 35 / 28 和 rgthree 对比器 23 一并摘除：
  平台一次最多 2 张图，多留会撞上限，也会拖慢出图。
- 2026-09-29 工作流换版：新增 SeedVR2 分块放大链（1047 / 1048 / 1064 / 1073 / 1076 /
  1079 / 1089 / 1090 / 1095 / 1096 / 1098 / 1099 / 1109 / 1110 / 1111），末端
  SaveImage 1100 出放大图，输入取自 21。链上的 PreviewImage 1101 ~ 1103 落 Comfy
  temp、不计入产物，但它们是输出节点，不摘 Comfy 就会真跑这条链——本能力要这张放大图，
  所以照原样保留。
"""
import os

from django.conf import settings

from 能力.工作流工具 import (装载工作流, 按类型找节点, 写参数, 上传到Comfy,
                            摘除节点, 任务文件, 随机种子)

工作流文件 = 'Qwen Edit 2511 双图编辑【一致性加强版】电商_摄影等 (3).json'

# 页面上传位 → (LoadImage 节点, QwenEditConfigPreparer 节点,
#                QwenEditAdaptiveLongestEdge 节点, task 列名, 说明)。
# 顺序 = 页面上的 图1/图2/图3，也是 refs 链的顺序（链头 = 主图）。
图位 = (
    ('13', '15', '9', '输入图1', '主图'),
    ('12', '14', '11', '输入图2', '参考图'),
    ('32', '34', '33', '输入图3', '参考图'),
)

# 摘除：拼接对比图保存链 + rgthree 对比器
摘除清单 = ('25', '24', '35', '28', '23')

# 产物两个：22 成品（产物图片）、1100 SeedVR2 分块放大后（产物图片2）
放大后 = '1100'


def 构建三图编辑一致版(任务, comfy_url):
    # 1~3 张柔性：图1（主图）必填，图2/图3 可选
    已填 = [位 for 位 in 图位 if getattr(任务, 位[3])]
    if not 已填 or 已填[0][3] != '输入图1':
        raise ValueError('三图编辑一致版至少要上传图1（主图）。')

    路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 工作流文件)
    api = 装载工作流(路径)

    # 装图：只给已填的图位写 LoadImage
    for 节点id, _preparer, _长边, 列名, _说明 in 已填:
        文件 = str(任务文件(getattr(任务, 列名)))
        名字 = 上传到Comfy(comfy_url, 文件) if os.path.isfile(文件) else 文件
        写参数(api, 节点id, 'image', 名字)

    # 摘除没填的图位：Preparer + AdaptiveLongestEdge + LoadImage 整支摘掉
    已填节点 = {位[0] for 位 in 已填}
    for 节点id, preparer, 长边, _列名, 说明 in 图位:
        if 节点id in 已填节点:
            continue
        for nid in (preparer, 长边, 节点id):
            摘除节点(api, nid)

    for nid in 摘除清单:
        摘除节点(api, nid)

    # 重接 refs 链：第一个已填图位的 Preparer 是链头（无 configs），后面每个指向前一个，
    # 节点 10 吃最后一个。必须放在所有 摘除节点() 之后——摘除会删掉指向被摘节点的输入键。
    for 序号, (_节点id, preparer, _长边, _列名, _说明) in enumerate(已填):
        if 序号 == 0:
            api[preparer].setdefault('inputs', {}).pop('configs', None)
        else:
            api[preparer].setdefault('inputs', {})['configs'] = [已填[序号 - 1][1], 0]
    写参数(api, '10', 'configs', [已填[-1][1], 0])

    # 提示词：后端只 rstrip，不在后端拼接
    if 任务.正向提示词:
        写参数(api, '8', 'value', 任务.正向提示词.rstrip())

    种子 = 任务.seed if 任务.seed is not None else 随机种子()
    for nid in 按类型找节点(api, 'KSampler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子
    # 1111 SeedVR2 也有 seed（工作流自带默认 100），不写就永远是 100
    for nid in 按类型找节点(api, 'SeedVR2VideoUpscaler'):
        api[nid].setdefault('inputs', {})['seed'] = 种子

    # 两张图分别落前缀：提交并等待 按放大标记 _hd 分流到 产物图片 / 产物图片2
    写参数(api, '22', 'filename_prefix', 'aicg_edit2511')
    写参数(api, 放大后, 'filename_prefix', 'aicg_edit2511_hd')
    return api
