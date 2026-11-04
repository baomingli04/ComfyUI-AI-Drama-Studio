# -*- coding: utf-8 -*-
"""把 6 个模式的图交给**插件自己的 build_director_plan** 跑一遍（纯 CPU，不采样）。

前两步自检（_t_全能六模式 / _t_图校验）只能证明「字段是我想要的」和「ComfyUI 认这些枚举」，
都不能证明「插件的 plan 构建器会照我预期解读这份 timeline_data」。
真正的分歧点全在 plan 里：段怎么切、refs 走 global 还是段级、源片怎么变 <Video 1>、
i2v 的图有没有被当成第 0 帧……这些只有让插件自己算一遍才知道。

分两步跑（两边的 Python 不是同一个）：
  1. 本脚本：用 Django 环境构建 6 个 API 图，把 timeline_data + 标量参数 dump 成 JSON
  2. `_t_plan构建.py`（用 ComfyUI 的 python 跑）：import director.plan 调 build_director_plan

素材用 ComfyUI/input 里的 `_t_plan_*`（脚本会自己检查在不在）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.stdout.reconfigure(encoding='utf-8')

import django  # noqa: E402

django.setup()

import 能力.导演台全能 as 全能  # noqa: E402

输入目录 = 'D:/ComfyUI-aki-v3/ComfyUI/input'
首帧 = '_t_plan_首帧.png'
尾帧 = '_t_plan_尾帧.png'
参考图 = '_t_plan_参考1.png'
源片 = '_t_plan_源片.mp4'
参考音 = '_t_plan_参考音.wav'

for 名 in (首帧, 尾帧, 参考图, 源片, 参考音):
    if not os.path.exists(os.path.join(输入目录, 名)):
        raise SystemExit('缺少测试素材：%s（先跑 _t_plan素材.sh 或手工 ffmpeg）' % 名)

# 打桩：上传直接返回文件名（文件已经在 ComfyUI/input 里，插件会自己去那儿读）
全能.上传到Comfy = lambda comfy_url, 路径: os.path.basename(str(路径))
全能.任务文件 = lambda p: p


class 假任务:
    def __init__(self, 模式, 图=(), 视频=(), 音频=(), 时长=5, 提示词='测试提示词'):
        self.模式 = 模式
        self.正向提示词 = 提示词
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
            setattr(self, '输入图%d' % i, 图[i - 1] if i <= len(图) else '')
        for i in range(1, 4):
            setattr(self, '输入视频%d' % i, 视频[i - 1] if i <= len(视频) else '')
            setattr(self, '输入音频%d' % i, 音频[i - 1] if i <= len(音频) else '')


用例 = [
    ('t2v', dict()),
    ('i2v', dict(图=(首帧,))),
    ('fl2v', dict(图=(首帧, 尾帧))),
    ('r2v', dict(图=(参考图, 参考图), 音频=(参考音,))),
    ('v2v', dict(视频=(源片,))),
    ('rv2v', dict(图=(参考图,), 视频=(源片,), 音频=(参考音,))),
]

输出 = {}
for 模式, kw in 用例:
    任务 = 假任务(模式, **kw)
    api = 全能.构建导演台全能(任务, 'http://127.0.0.1:8188')
    导演 = None
    for 节点id, 节点 in api.items():
        if 节点.get('class_type') == 'MiniMaxH3Director':
            导演 = 节点['inputs']
            break
    输出[模式] = {
        'timeline_data': 导演['timeline_data'],
        'global_task_type': 导演['task_type'],
        'global_prompt': 导演['global_prompt'],
        'total_frames': 导演['total_frames'],
        'frame_rate': 导演['frame_rate'],
        'width': 导演['width'],
        'height': 导演['height'],
        'ref_max_size': 导演['ref_max_size'],
    }

路径 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_t_plan输入.json')
with open(路径, 'w', encoding='utf-8') as f:
    json.dump(输出, f, ensure_ascii=False, indent=1)
print('已写出 %s（6 个模式）' % 路径)
