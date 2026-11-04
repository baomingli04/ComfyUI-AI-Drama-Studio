# -*- coding: utf-8 -*-
"""用**插件自己的** build_director_plan 解读 _t_plan输入.json 里 6 份 timeline_data。

必须用 ComfyUI 的 python 跑（要有 torch / folder_paths）：
    D:/ComfyUI-aki-v3/python/python.exe _t_plan构建.py

只做 CPU 侧的读图/读视频帧与计划拼装，不采样、不加载 UNET、不碰显存。
"""
import json
import os
import sys
import types
import importlib

sys.stdout.reconfigure(encoding='utf-8')

COMFY_ROOT = 'D:/ComfyUI-aki-v3/ComfyUI'
插件目录 = os.path.join(COMFY_ROOT, 'custom_nodes', 'ComfyUI_MiniMaxH3_Director')
sys.path.insert(0, COMFY_ROOT)

# 插件内部用的是 `from ..lib.audio_io import ...`（相对两层），所以必须把它当包导入。
# 但直接 `import ComfyUI_MiniMaxH3_Director` 会执行它的 __init__.py（注册全部节点、
# 依赖 comfy 的运行时上下文），这里不需要。做法：造一个只有 __path__ 的空包占位，
# 让相对导入能解析，同时跳过 __init__.py。
包名 = 'H3插件'
占位 = types.ModuleType(包名)
占位.__path__ = [插件目录]
sys.modules[包名] = 占位

build_director_plan = importlib.import_module(包名 + '.director.plan').build_director_plan

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_t_plan输入.json'),
          encoding='utf-8') as f:
    用例 = json.load(f)

for 模式, 参数 in 用例.items():
    print('\n' + '=' * 60)
    print('模式 %s   global_task_type=%s' % (模式, 参数['global_task_type']))
    try:
        plan = build_director_plan(
            参数['timeline_data'],
            global_task_type=参数['global_task_type'],
            global_prompt=参数['global_prompt'],
            total_frames=参数['total_frames'],
            frame_rate=参数['frame_rate'],
            width=参数['width'],
            height=参数['height'],
            ref_max_size=参数['ref_max_size'],
        )
    except Exception as e:
        print('  ✗ 构建失败：%s: %s' % (type(e).__name__, e))
        continue

    print('  ✓ 计划：%d 段 / 总帧 %d / %dx%d / output_mode=%s / edit_mode=%s'
          % (len(plan.segments), plan.total_frames, plan.width, plan.height,
             plan.output_mode, plan.edit_mode))
    print('    global_task_key=%s  source_total=%d  continuity=%s(overlap=%d)'
          % (plan.global_task_key, plan.source_total_frames,
             plan.continuity_enabled, plan.continuity_overlap_frames))
    print('    source_video shape=%s' % (tuple(plan.source_video.shape),))
    for seg in plan.segments:
        源片 = tuple(seg.source_clip.shape) if seg.source_clip is not None else None
        print('    段%d  task=%-6s 帧[%d,%d)=%d  refs=%d  refAudio=%d  源clip=%s  prompt=%r'
              % (seg.index, seg.task_key, seg.start_frame, seg.end_frame,
                 seg.frame_count, len(seg.refs), len(seg.ref_audios), 源片,
                 (seg.prompt or '')[:16]))
        if seg.refs:
            print('         refs 编号: %s' % [r.index for r in seg.refs])

print('\n' + '=' * 60)
print('说明：段数/帧区间/task_key/refs 编号就是插件真正会拿去采样用的东西。')
