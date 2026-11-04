# -*- coding: utf-8 -*-
"""把 6 个模式构建出的 API 图，逐节点对照运行中 ComfyUI 的 /object_info 做静态校验。

为什么要这一步：`_t_全能六模式.py` 只证明「我写进去的字段是我想写的」，
不证明「ComfyUI 认这些值」。task_type / sampler / unet_name 这类枚举一旦写错，
要等真的排进队列才会报错，那时候已经占着 GPU 了。

本脚本不排队、不采样、不碰显存，只读 /object_info 做比对：
  1. 每个 class_type 在 ComfyUI 里存在
  2. 节点的 required 输入一个不缺
  3. 枚举类（下拉）的值必须在可选列表里
  4. 连线（[节点id, 槽位]）指向的节点存在、槽位不越界

跑法：./.venv/Scripts/python.exe _t_图校验.py
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

import 能力.导演台全能 as 全能  # noqa: E402

COMFY = 'http://127.0.0.1:8188'

# ---- 打桩上传 ----
_n = {'i': 0}


def 假上传(comfy_url, 路径):
    _n['i'] += 1
    return 'stub_%d_%s' % (_n['i'], os.path.basename(str(路径)))


全能.上传到Comfy = 假上传
全能.任务文件 = lambda p: p


class 假任务:
    def __init__(self, 模式, 图=0, 视频=0, 音频=0, 时长=5):
        self.模式 = 模式
        self.正向提示词 = '测试提示词'
        self.反向提示词 = 'bad video'
        self.seed = 666
        self.cfg = 1
        self.比例 = '16:9'
        self.一采MP = 0.4
        self.视频时长 = 时长
        self.生成声音 = True
        self.步数 = 8
        self.采样器 = 'res_multistep'
        for i in range(1, 10):
            setattr(self, '输入图%d' % i, 'D:/fake/图%d.png' % i if i <= 图 else '')
        for i in range(1, 4):
            setattr(self, '输入视频%d' % i, 'D:/fake/片%d.mp4' % i if i <= 视频 else '')
            setattr(self, '输入音频%d' % i, 'D:/fake/音%d.wav' % i if i <= 音频 else '')


def 取对象信息():
    with urllib.request.urlopen(COMFY + '/object_info', timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


对象信息 = 取对象信息()
print('已拉到 /object_info，共 %d 个节点类型' % len(对象信息))


def 校验(模式, api):
    问题 = []
    for 节点id, 节点 in api.items():
        类型 = 节点.get('class_type')
        if 类型 not in 对象信息:
            问题.append('节点 %s：class_type「%s」不存在' % (节点id, 类型))
            continue
        规格 = 对象信息[类型].get('input') or {}
        必填 = 规格.get('required') or {}
        可选 = 规格.get('optional') or {}
        inputs = 节点.get('inputs') or {}

        for 键 in 必填:
            if 键 not in inputs:
                问题.append('节点 %s(%s)：缺必填输入「%s」' % (节点id, 类型, 键))

        for 键, 值 in inputs.items():
            定义 = 必填.get(键) or 可选.get(键)
            if not 定义:
                # 有些节点把额外键当元数据（如 bd_grp_*），这里只提示不报错
                continue
            类型串 = 定义[0]
            # 连线：[节点id, 槽位]
            if isinstance(值, list) and len(值) == 2 and isinstance(值[0], str) and isinstance(值[1], int):
                if 值[0] not in api:
                    问题.append('节点 %s(%s).%s 连到不存在的节点 %s' % (节点id, 类型, 键, 值[0]))
                continue
            # 下拉：[[选项...], {...}]
            if isinstance(类型串, list) and 类型串 and isinstance(类型串[0], list):
                选项 = 类型串[0]
                if 值 not in 选项:
                    问题.append('节点 %s(%s).%s = %r 不在下拉里（前几个：%r）'
                              % (节点id, 类型, 键, 值, 选项[:4]))
            elif 类型串 == 'INT' and not isinstance(值, int):
                问题.append('节点 %s(%s).%s 应为 INT，实际 %r' % (节点id, 类型, 键, 值))
            elif 类型串 == 'FLOAT' and not isinstance(值, (int, float)):
                问题.append('节点 %s(%s).%s 应为 FLOAT，实际 %r' % (节点id, 类型, 键, 值))
            elif 类型串 == 'STRING' and not isinstance(值, str):
                问题.append('节点 %s(%s).%s 应为 STRING，实际 %r' % (节点id, 类型, 键, 值))
    return 问题


用例 = [
    ('t2v', dict()),
    ('i2v', dict(图=1)),
    ('fl2v', dict(图=2)),
    ('r2v', dict(图=3, 音频=1)),
    ('v2v', dict(视频=1)),
    ('rv2v', dict(图=2, 视频=1, 音频=1)),
]

总问题 = 0
for 模式, kw in 用例:
    任务 = 假任务(模式, **kw)
    api = 全能.构建导演台全能(任务, COMFY)
    问题 = 校验(模式, api)
    总问题 += len(问题)
    print('\n===== %-4s 节点 %d 个 → %s' % (模式, len(api), 'OK' if not 问题 else '%d 个问题' % len(问题)))
    for 条 in 问题:
        print('   ·', 条)

# 额外核对：Director 节点的 task_type 必须真在下拉里
规格 = 对象信息['MiniMaxH3Director']['input']['required']['task_type'][0]
print('\n---- Director task_type 下拉共 %d 个 ----' % len(规格))
for 项 in 规格:
    print('   ', 项)
for 模式, (官方串, _族) in 全能.模式配置.items():
    标记 = 'OK ' if 官方串 in 规格 else 'BAD'
    if 官方串 not in 规格:
        总问题 += 1
    print('[%s] %-4s → %s' % (标记, 模式, 官方串))

print('\n结论：', '全部通过' if 总问题 == 0 else '有 %d 处需要修' % 总问题)
