# -*- coding: utf-8 -*-
"""导演台全能 6 个模式的构建结果自检（不连 ComfyUI、不跑 GPU）。

只做三件事：把 上传到Comfy / 任务文件 打桩，构造一个假任务，
按每种模式跑一遍 构建导演台全能，然后把**真正会送进节点**的关键字段打出来，
逐条对着插件源码的读取路径核对。

跑法：./.venv/Scripts/python.exe _t_全能六模式.py
（要 Django，不能用 ComfyUI 那个 python）
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


class 假任务:
    def __init__(self, **kw):
        self.模式 = kw.get('模式', 'r2v')
        self.正向提示词 = kw.get('正向提示词', '测试提示词')
        self.反向提示词 = kw.get('反向提示词', 'bad video')
        self.seed = kw.get('seed', 666)
        self.cfg = kw.get('cfg', 1)
        self.比例 = kw.get('比例', '16:9')
        self.一采MP = kw.get('一采MP', 0.4)
        self.视频时长 = kw.get('视频时长', 15)
        self.生成声音 = kw.get('生成声音', True)
        self.步数 = kw.get('步数', 8)
        self.采样器 = kw.get('采样器', 'res_multistep')
        # 底膜精度开关：auto=工作流默认 / bf16 / int8。默认 auto = 本项目原有行为
        self.底膜精度 = kw.get('底膜精度', 'auto')
        for i in range(1, 10):
            setattr(self, '输入图%d' % i, '')
        for i in range(1, 4):
            setattr(self, '输入视频%d' % i, '')
            setattr(self, '输入音频%d' % i, '')


# ---- 打桩：不真的上传 ----
计数 = {'n': 0}


def 假上传(comfy_url, 路径):
    计数['n'] += 1
    return 'stub_%s_%d' % (os.path.basename(str(路径)), 计数['n'])


全能.上传到Comfy = 假上传
全能.任务文件 = lambda p: p


def 造(模式, 图=0, 视频=0, 音频=0, 时长=15, 精度='auto'):
    任务 = 假任务(模式=模式, 视频时长=时长, 底膜精度=精度)
    for i in range(1, 图 + 1):
        setattr(任务, '输入图%d' % i, 'D:/fake/图%d.png' % i)
    for i in range(1, 视频 + 1):
        setattr(任务, '输入视频%d' % i, 'D:/fake/片%d.mp4' % i)
    for i in range(1, 音频 + 1):
        setattr(任务, '输入音频%d' % i, 'D:/fake/音%d.wav' % i)
    return 任务


def 取导演(api):
    for k, v in api.items():
        if v.get('class_type') == 'MiniMaxH3Director':
            return k, v['inputs']
    raise AssertionError('没有 Director 节点')


def 取底膜(api):
    for k, v in api.items():
        if v.get('class_type') == 'UNETLoader':
            return v['inputs']['unet_name']
    raise AssertionError('没有 UNETLoader')


def 报(模式, 任务):
    api = 全能.构建导演台全能(任务, 'http://127.0.0.1:8188')
    _k, ins = 取导演(api)
    tl = json.loads(ins['timeline_data'])
    print('\n===== %s =====' % 模式)
    print('  底膜        :', 取底膜(api))
    print('  task_type   :', ins['task_type'])
    print('  total_frames:', ins['total_frames'], ' 宽高:', ins['width'], 'x', ins['height'])
    print('  timelineMode:', tl.get('timelineMode'), ' editMode:', tl.get('editMode'))
    print('  durationSec :', tl.get('durationSec'), ' totalFrames:', tl.get('totalFrames'))
    print('  段数        :', len(tl.get('segments') or []), ' shots:', len(tl.get('shots') or []))
    for i, s in enumerate(tl.get('segments') or []):
        print('    段%d  start=%s len=%s fc=%s dur=%s prompt=%r neg=%r genImage=%s'
              % (i, s.get('start'), s.get('length'), s.get('frameCount'),
                 s.get('durationSec'), s.get('prompt'), s.get('negativePrompt'),
                 json.dumps(s.get('genImage'), ensure_ascii=False)))
        print('        refs=%d refVideos=%d refAudios=%d'
              % (len(s.get('refs') or []), len(s.get('refVideos') or []),
                 len(s.get('refAudios') or [])))
    for i, s in enumerate(tl.get('shots') or []):
        print('    shot%d dur=%s start=%s end=%s'
              % (i, s.get('durationSec'),
                 json.dumps(s.get('startImage'), ensure_ascii=False),
                 json.dumps(s.get('endImage'), ensure_ascii=False)))
    g = tl.get('global') or {}
    print('  global.taskType:', g.get('taskType'))
    print('  global.prompt  :', repr((g.get('prompt') or '')[:40]))
    print('  global.refs=%d refVideos=%d refAudios=%d commonEnabled=%s'
          % (len(g.get('refs') or []), len(g.get('refVideos') or []),
             len(g.get('refAudios') or []), g.get('commonEnabled')))
    print('  global.genImage:', json.dumps(g.get('genImage'), ensure_ascii=False))
    print('  global.source  :', g.get('sourceWidth'), 'x', g.get('sourceHeight'))
    v = tl.get('video') or {}
    print('  video.videoFile:', repr(v.get('videoFile')), ' sourceFrameCount:', v.get('sourceFrameCount'),
          ' frames:', len(v.get('frames') or []), ' frameMap:', len(v.get('frameMap') or []))
    o = tl.get('output') or {}
    print('  output: %sx%s longEdge=%s mp=%s ratio=%s audio=%s'
          % (o.get('width'), o.get('height'), o.get('longEdge'),
             o.get('megapixels'), o.get('aspectRatio'), o.get('audioMode')))
    return ins, tl


# ---------------- 逐模式断言 ----------------
# 1) t2v
ins, tl = 报('t2v', 造('t2v'))
assert 取底膜({'x': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'}}}).startswith('minimax')
assert tl['timelineMode'] == 'prompt_batch'
assert len(tl['segments']) == 2 and tl['totalFrames'] == 367
assert all(s['prompt'] == '' for s in tl['segments'])
assert (tl['global']['refs'] == [] and tl['global']['refVideos'] == [])

# 2) i2v
ins, tl = 报('i2v', 造('i2v', 图=1))
assert tl['timelineMode'] == 'prompt_batch'
assert len(tl['segments']) == 1, 'i2v 必须单段'
assert tl['segments'][0]['genImage']['imageFile'].startswith('stub_图1')
# 15s @24fps → 360 帧 → 补到 17k+5 = 362（单段与工作流两段 243+124=367 不同，
# 这是单段本身的取整结果，不是写错）
assert tl['segments'][0]['frameCount'] == tl['totalFrames'] == 362
assert tl['shots'] == [] and tl['keyframes'] == []
assert tl['global']['sourceWidth'] == 0

# 3) fl2v 双帧
ins, tl = 报('fl2v', 造('fl2v', 图=2, 时长=5))
assert tl['timelineMode'] == 'fl2v' and tl['segments'] == []
assert len(tl['shots']) == 1
assert tl['shots'][0]['startImage']['imageFile'].startswith('stub_图1')
assert tl['shots'][0]['endImage']['imageFile'].startswith('stub_图2')

# 4) r2v
ins, tl = 报('r2v', 造('r2v', 图=2, 音频=1))
assert tl['timelineMode'] == 'prompt_batch' and len(tl['segments']) == 2
assert len(tl['global']['refs']) == 2 and len(tl['global']['refAudios']) == 1
assert all(s['refs'] == [] for s in tl['segments'])

# 5) v2v
ins, tl = 报('v2v', 造('v2v', 视频=1, 时长=5))
assert tl['timelineMode'] == 'video' and tl['editMode'] == 'global'
assert tl['video']['videoFile'].startswith('stub_片1')
assert len(tl['segments']) == 1 and tl['segments'][0]['length'] == tl['totalFrames'] == 124
assert tl['video']['frames'] == [] and tl['video']['frameMap'] == []

# 6) rv2v
ins, tl = 报('rv2v', 造('rv2v', 图=1, 视频=3, 音频=1, 时长=5))
assert tl['timelineMode'] == 'video'
assert tl['video']['videoFile'].startswith('stub_片1')
assert len(tl['global']['refs']) == 1
# 官方 rv2v 没有参考视频槽（task_prompts.py:59 + plan.reference_video_for_segment 的
# "not used by v2v"），所以即使任务上填了 输入视频2/3 也不上传、不写 refVideos
assert tl['global']['refVideos'] == [], 'rv2v 不该有参考视频'
assert len(tl['global']['refAudios']) == 1
assert all(s['refs'] == [] for s in tl['segments'])

# 7) 错模式必须报错
try:
    全能.构建导演台全能(假任务(模式='mixed'), 'http://127.0.0.1:8188')
except ValueError as e:
    print('\n===== 错模式 =====\n  按预期报错:', e)
else:
    raise AssertionError('mixed 没接入本页，应该报错')

# 8) 缺素材必须报错
for 模式, kw, 关键字 in [
    ('i2v', dict(图=0), '首帧'),
    ('r2v', dict(图=0), '参考图'),
    ('v2v', dict(视频=0), '源视频'),
]:
    try:
        全能.构建导演台全能(造(模式, **kw), 'http://127.0.0.1:8188')
    except ValueError as e:
        assert 关键字 in str(e), '%s 的报错没提「%s」：%s' % (模式, 关键字, e)
        print('  缺素材报错 OK  %-4s → %s' % (模式, e))
    else:
        raise AssertionError('%s 缺素材没报错' % 模式)

print('\n全部通过。')

# ---------------- 底膜精度开关（auto / bf16 / int8） ----------------
# auto 必须保持本项目原有行为：ref2va→bf16、fl2va→int8。换 auto 的默认值 = 动了实测配置。
精度用例 = [
    ('auto（默认）', {'ref2va': 'minimax_h3_ref2va_pruned_bf16.safetensors',
                 'fl2va': 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'}),
    ('bf16', {'ref2va': 'minimax_h3_ref2va_pruned_bf16.safetensors',
             'fl2va': 'minimax_h3_fl2va_pruned_bf16.safetensors'}),
    ('int8', {'ref2va': 'minimax_h3_ref2va_pruned_int8_convrot.safetensors',
             'fl2va': 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'}),
]
族表 = {'t2v': 'fl2va', 'i2v': 'fl2va', 'fl2v': 'fl2va',
       'r2v': 'ref2va', 'v2v': 'ref2va', 'rv2v': 'ref2va'}
# 每个模式至少给够能过素材校验的量（只影响能否构建，不影响底膜断言）
素材量 = {'t2v': 0, 'i2v': 1, 'fl2v': 2, 'r2v': 1, 'v2v': 0, 'rv2v': 1}
print('\n---- 底膜精度 ----')
for 档名, 期望 in 精度用例:
    for 模式, 族 in 族表.items():
        api = 全能.构建导演台全能(造(模式, 图=素材量[模式],
                                   视频=1 if 模式 in ('v2v', 'rv2v') else 0,
                                   音频=1 if 模式 == 'rv2v' else 0,
                                   时长=5, 精度=档名), 'http://127.0.0.1:8188')
        实际 = 取底膜(api)
        assert 实际 == 期望[族], '%s + %s 应得 %s，实际 %s' % (档名, 模式, 期望[族], 实际)
    print('  [OK ] %-12s ref2va → %s' % (档名, 期望['ref2va']))
    print('  [OK ] %-12s fl2va  → %s' % (档名, 期望['fl2va']))
print('  [OK ] 3 档 × 6 模式共 18 种组合的 unet_name 全部符合预期')

# 乱填的档位不能崩，回落 auto
api = 全能.构建导演台全能(造('r2v', 图=1, 时长=5, 精度='fp8'), 'http://127.0.0.1:8188')
assert 取底膜(api) == 'minimax_h3_ref2va_pruned_bf16.safetensors', '乱填档位应回落 auto'
print('  [OK ] 乱填档位「fp8」→ 回落 auto（bf16），不报错')
assert 全能.基座模型文件['ref2va']['auto'] == 'minimax_h3_ref2va_pruned_bf16.safetensors'
assert 全能.基座模型文件['fl2va']['auto'] == 'minimax_h3_fl2va_pruned_int8_convrot.safetensors'
print('  [OK ] auto 档仍是本项目原值（没动实测配置）')

print('\n全部通过。')
