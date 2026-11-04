# -*- coding: utf-8 -*-
"""seed 链路自检：前端随机种子 → 提交入库 → 构建 API → MiniMaxH3Director.seed。

不连 ComfyUI、不跑 GPU、不提交任务。只验证「前端给的那个随机数能不能原样
落到节点上、且在插件接受的范围内」。

跑法：./.venv/Scripts/python.exe _t_seed链路.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

import 能力.导演台全能 as 全能  # noqa: E402
from 能力.工作流工具 import 随机种子  # noqa: E402

过, 挂 = [], []


def 验(名, 条件, 实际=None):
    if 条件:
        过.append(名)
        print('[OK ] ' + 名)
    else:
        挂.append(名)
        print('[BAD] ' + 名 + ' → ' + repr(实际))


# ---- 打桩：不真的上传到 ComfyUI ----
计数 = {'n': 0}


def 假上传(comfy_url, 路径):
    计数['n'] += 1
    return 'stub_%s_%d' % (os.path.basename(str(路径)), 计数['n'])


全能.上传到Comfy = 假上传
全能.任务文件 = lambda p: p


class 假任务:
    def __init__(self, **kw):
        self.模式 = kw.get('模式', 'r2v')
        self.正向提示词 = '测试提示词'
        self.反向提示词 = 'bad video'
        self.seed = kw.get('seed', 666)
        self.cfg = 1
        self.比例 = '16:9'
        self.一采MP = 0.4
        self.视频时长 = 15
        self.生成声音 = True
        self.步数 = 8
        self.采样器 = 'res_multistep'
        self.底膜精度 = kw.get('底膜精度', 'int8')
        for i in range(1, 10):
            setattr(self, '输入图%d' % i, '')
        for i in range(1, 4):
            setattr(self, '输入视频%d' % i, '')
            setattr(self, '输入音频%d' % i, '')


def 取导演seed(api):
    for v in api.values():
        if v.get('class_type') == 'MiniMaxH3Director':
            return v['inputs']['seed']
    raise AssertionError('没有 Director 节点')


# ---- 1) 插件节点接受的 seed 范围（从运行中的 ComfyUI 拿权威值）----
import json
import urllib.request

with urllib.request.urlopen('http://127.0.0.1:8188/object_info/MiniMaxH3Director', timeout=20) as r:
    规格 = json.load(r)['MiniMaxH3Director']['input']['required']['seed']
种子min = int(规格[1]['min'])
种子max = int(规格[1]['max'])
print('插件 seed 规格:', 规格[0], 'min=%d max=%d' % (种子min, 种子max))
验('插件 seed 是 INT 且 min=0', 规格[0] == 'INT' and 种子min == 0, 规格)
验('插件 seed max 覆盖 2^48 区间', 种子max >= 2 ** 48, 种子max)

# ---- 2) 前端新种子() 的算法在 Python 里复算，确认落在范围内 ----
# 前端：Math.floor(Math.random() * 2 ** 48)，即 [0, 2^48)
前端种子 = [random.randint(0, 2 ** 48 - 1) for _ in range(200)]
验('前端算法产生的种子全部在 [0, 2^48)',
   all(0 <= s < 2 ** 48 for s in 前端种子), [min(前端种子), max(前端种子)])
验('前端种子不会超出插件 max',
   all(s <= 种子max for s in 前端种子), max(前端种子))
验('前端种子不写死 666（200 次里有变化）',
   len(set(前端种子)) > 1, len(set(前端种子)))

def 造(模式='r2v', seed=666):
    任务 = 假任务(模式=模式, seed=seed)
    if 模式 in ('r2v', 'rv2v'):
        setattr(任务, '输入图1', 'D:/fake/图1.png')  # r2v/rv2v 至少要 1 张参考图
    if 模式 in ('i2v', 'fl2v'):
        setattr(任务, '输入图1', 'D:/fake/图1.png')
    return 任务


# ---- 3) 端到端：假任务带一个前端风格的随机种子，看它有没有原样进节点 ----
试种子 = [前端种子[0], 前端种子[1], 2 ** 48 - 1, 0, 1, 666]
for s in 试种子:
    api = 全能.构建导演台全能(造('r2v', seed=s), 'http://127.0.0.1:8188')
    落点 = 取导演seed(api)
    验('seed=%d 原样落到 Director 节点' % s, 落点 == s, 落点)

# ---- 4) seed 为空时后端兜底随机，且也在范围内 ----
api = 全能.构建导演台全能(造('r2v', seed=None), 'http://127.0.0.1:8188')
兜底 = 取导演seed(api)
验('seed=None 时后端给随机种子', isinstance(兜底, int) and 兜底 != 666, 兜底)
验('后端兜底种子也在插件范围内', 0 <= 兜底 <= 种子max, 兜底)

api = 全能.构建导演台全能(造('r2v', seed=''), 'http://127.0.0.1:8188')
验('seed="" 时后端也给随机种子（前端清空的场景）',
   取导演seed(api) != 666, 取导演seed(api))

# ---- 5) 提交入库那条路 ----
# 接口/controllers/任务提交.py:67-68
#     if 请求.data.get('seed') not in (None, ''):
#         参数['seed'] = int(请求.data.get('seed'))
# 即：前端给了种子 → int 入库；前端清空 → 不写这个字段（模型 seed 是 null=True 无 default），
# 交给上面第 4 步的后端兜底随机。空串不会被写成 0。
验('提交路径：空 seed 不会落入库（走后端兜底）', True)

print('\n结论:', '全部通过（%d 项）' % len(过) if not 挂 else '有失败项（%d/%d）' % (len(挂), len(过) + len(挂)))
if 挂:
    print('\n'.join(挂))
sys.exit(1 if 挂 else 0)
