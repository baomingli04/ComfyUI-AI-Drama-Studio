# -*- coding: utf-8 -*-
"""临时对拍：用前端默认表单跑 构建导演台全能，逐字段对比工作流原值。

目的：确认「网页默认值 == 工作流默认值」，并且没有被重算/覆盖的字段。
跑法：.venv\\Scripts\\python.exe _t_director_defaults.py
"""
import json
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.conf import settings
import 能力.导演台全能 as 能力

工作流路径 = os.path.join(str(settings.RESOURCE_DIR / '工作流'), 能力.工作流文件)
原 = json.load(open(工作流路径, encoding='utf-8'))
原td = json.loads(原['12']['inputs']['timeline_data'])


class 假任务:
    """模拟前端默认表单（index.js 里的 表单）。"""

    def __init__(self, 模式='r2v', 有图=True):
        self.模式 = 模式
        self.输入图1 = '上传/a.png' if 有图 else ''
        self.输入图2 = '上传/b.png' if 有图 else ''
        for i in range(3, 10):
            setattr(self, '输入图%d' % i, '')
        for i in range(1, 4):
            setattr(self, '输入视频%d' % i, '')
            setattr(self, '输入音频%d' % i, '')
        self.正向提示词 = '测试提示词：一个人在雨中奔跑'
        self.反向提示词 = 'bad video'
        self.seed = 666
        self.cfg = 1
        self.比例 = '16:9'
        self.一采MP = 0.4
        self.视频时长 = 15
        self.生成声音 = True
        self.步数 = 8
        self.采样器 = 'res_multistep'


# 上传直接返回假文件名，避免真连 ComfyUI
能力.上传到Comfy = lambda comfy_url, path: 'fake_' + os.path.basename(str(path))


def 对比(模式, 有图=True):
    api = 能力.构建导演台全能(假任务(模式, 有图), 'http://127.0.0.1:8188')
    n1 = api['1']['inputs']
    n12 = api['12']['inputs']
    td = json.loads(n12['timeline_data'])

    print('=' * 70)
    print('模式 =', 模式)
    print('-' * 70)
    print('%-26s %-42s %s' % ('字段', '工作流原值', '本次构建值'))
    对 = []

    def 行(名, 新, 旧):
        同 = '  同' if 新 == 旧 else '★差异'
        print('%-26s %-42s %-42s %s' % (名, str(旧)[:40], str(新)[:40], 同))
        if 新 != 旧:
            对.append(名)

    # 底膜
    行('1.unet_name', n1['unet_name'], 原['1']['inputs']['unet_name'])
    # 加速链：必须原样
    行('17.sage_attention', api['17']['inputs']['sage_attention'], 原['17']['inputs']['sage_attention'])
    行('17.allow_compile', api['17']['inputs']['allow_compile'], 原['17']['inputs']['allow_compile'])
    行('25.lora_name', api['25']['inputs']['lora_name'], 原['25']['inputs']['lora_name'])
    行('25.strength_model', api['25']['inputs']['strength_model'], 原['25']['inputs']['strength_model'])
    # Director 标量
    for k in ('scheduler', 'shift_video', 'shift_audio', 'export_source_images',
              'export_pre_face_refine', 'clear_vram_before_face_refine'):
        行('12.' + k, n12[k], 原['12']['inputs'][k])
    行('12.steps', n12['steps'], 原['12']['inputs']['steps'])
    行('12.sampler', n12['sampler'], 原['12']['inputs']['sampler'])
    行('12.cfg', n12['cfg'], 原['12']['inputs']['cfg'])
    行('12.frame_rate', n12['frame_rate'], 原['12']['inputs']['frame_rate'])
    行('12.width', n12['width'], 原['12']['inputs']['width'])
    行('12.height', n12['height'], 原['12']['inputs']['height'])
    行('12.ref_max_size', n12['ref_max_size'], 原['12']['inputs']['ref_max_size'])
    行('12.total_frames', n12['total_frames'], 原['12']['inputs']['total_frames'])
    # timeline 结构字段
    for k in ('version', 'editMode', 'frameRate', 'width', 'height', 'refMaxSize',
              'durationSec', 'timelineMode', 'liveTaePreview', 'batchDetailMode'):
        行('td.' + k, td.get(k), 原td.get(k))
    行('td.totalFrames', td.get('totalFrames'), 原td.get('totalFrames'))
    for k in ('mode', 'megapixels', 'multiple', 'longEdge', 'width', 'height',
              'maxExportFrames', 'exportMode', 'audioMode', 'exportSourceImages',
              'exportPreFaceRefine', 'refImageSize', 'continuityEnabled',
              'continuityOverlapFrames', 'continuityMode', 'continuityRedraw',
              'continuityKeepTail'):
        行('td.output.' + k, (td.get('output') or {}).get(k), (原td.get('output') or {}).get(k))
    行('td.output.aspectRatio', (td.get('output') or {}).get('aspectRatio'),
       (原td.get('output') or {}).get('aspectRatio'))
    行('td.global.commonEnabled', (td.get('global') or {}).get('commonEnabled'),
       (原td.get('global') or {}).get('commonEnabled'))
    行('td.global.taskType', (td.get('global') or {}).get('taskType'),
       (原td.get('global') or {}).get('taskType'))
    # 分段
    原段 = 原td.get('segments') or []
    新段 = td.get('segments') or []
    print('%-26s %-42s %s' % ('td.segments 帧数',
                              [s.get('frameCount') for s in 原段],
                              [s.get('frameCount') for s in 新段]))
    print('%-26s %-42s %s' % ('td.segments 时长',
                              [s.get('durationSec') for s in 原段],
                              [s.get('durationSec') for s in 新段]))
    print('%-26s %-42s %s' % ('td.shots 数量', len(原td.get('shots') or []), len(td.get('shots') or [])))
    print('%-26s %-42s %s' % ('td.keyframes 数量', len(原td.get('keyframes') or []), len(td.get('keyframes') or [])))
    print('-' * 70)
    print('与工作流不一致的字段：', 对 if 对 else '无（全部一致）')
    return api, td


对比('r2v')
对比('t2v', 有图=False)
对比('fl2v')

# 单独看 fl2v 的 shots 是否正确带上首尾帧
api = 能力.构建导演台全能(假任务('fl2v'), 'http://127.0.0.1:8188')
td = json.loads(api['12']['inputs']['timeline_data'])
print('=' * 70)
print('fl2v shots =', json.dumps(td['shots'], ensure_ascii=False))
print('fl2v total_frames =', api['12']['inputs']['total_frames'],
      '| segments =', len(td['segments']), '| keyframes =', len(td['keyframes']))
