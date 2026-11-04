# -*- coding: utf-8 -*-
"""验证扩写后端按「模式 + 图数」选对分支：导演台六模式不能串格式。

用法：./.venv/Scripts/python.exe _t_扩写分支.py
"""
import os
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from 接口.controllers.提示词扩写 import _模式与替换规则, _读技能规范  # noqa: E402

# (说明, 后端模式, 图数, 必须出现, 必须不出现)
用例 = [
    ('t2v 无素材（0 图）', 'single_frame', 0, ['三段', 'integrated_multimodal_description'], ['subject_definitions']),
    # i2v：1 张图 → 后端 single_frame 的 I2VA 分支（与 fl2v 只首帧同一条路）
    ('i2v 单图（1 图）', 'single_frame', 1, ['I2VA', 'Picture 1'], ['subject_definitions']),
    ('fl2v 只首帧（1 图）', 'single_frame', 1, ['I2VA', 'Picture 1'], ['subject_definitions']),
    ('fl2v 首尾帧（2 图）', 'single_frame', 2, ['FL2VA', 'How the reference pictures align'], ['subject_definitions']),
    ('r2v 多参考（3 图）', 'multi_reference', 3, ['subject_definitions', 'retention_analysis'], ['How the reference pictures align']),
    ('r2v 九图三视频三音频', 'multi_reference', 9, ['subject_definitions'], ['integrated_multimodal_description']),
    # v2v：只有源视频、没有图 → 走 single_frame 的 0 图分支（T2VA 三段式）。
    # 源视频在提示词里由页面规则追加的「本页当前状态」指定为 <Video 1>，
    # 后端这里只负责三段式骨架（源视频不占图数，所以不能算成 1 图走 I2VA）。
    ('v2v 只有源视频（0 图）', 'single_frame', 0, ['integrated_multimodal_description', '三段'], ['I2VA', 'FL2VA', 'subject_definitions']),
    # rv2v：有图无图都走 multi_reference（无图那种由页面规则里的「没有参考图就别写 Subject」兜）
    ('rv2v 有参考图（1 图）', 'multi_reference', 1, ['subject_definitions', 'retention_analysis'], ['How the reference pictures align']),
    ('rv2v 无参考图（0 图）', 'multi_reference', 0, ['subject_definitions'], ['How the reference pictures align']),
]

全通过 = True
for 名, 模式, 图数, 必须有, 必须无 in 用例:
    规则, _替换 = _模式与替换规则(模式, 图数)
    缺 = [x for x in 必须有 if x not in 规则]
    多 = [x for x in 必须无 if x in 规则]
    通过 = not 缺 and not 多
    全通过 = 全通过 and 通过
    print('[%s] %-22s 模式=%-16s 图数=%d' % ('OK ' if 通过 else 'BAD', 名, 模式, 图数))
    if 缺:
        print('      缺少：', 缺)
    if 多:
        print('      不该出现：', 多)

print('\n---- 规范文件读取（决定读 base-en.txt 还是 ref-en.txt）----')
for 模式 in ('single_frame', 'multi_reference'):
    规范 = _读技能规范('h3-prompt-writing', 模式)
    头 = [行 for 行 in 规范.split('\n') if 行.startswith('# 规范文件')]
    print('%-16s → %s  总长 %d 字' % (模式, 头 or '(只读了 SKILL.md)', len(规范)))

print('\n结论：', '全部通过' if 全通过 else '有分支不对，需要检查')
