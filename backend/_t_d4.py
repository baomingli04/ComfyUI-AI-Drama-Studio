# -*- coding: utf-8 -*-
"""临时测试：直接跑一个「视频生视频」任务（最小化：256x160 / 1 秒）。"""
import os
import sys
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.utils import timezone
from 接口.models.task import task
from 能力.提交并等待 import _跑comfy任务

类型 = sys.argv[1] if len(sys.argv) > 1 else '视频生视频'

参数 = {
    '类型': 类型,
    '状态': '已创建',
    '创建时间': timezone.now(),
    '创建人id_id': 1,
    '正向提示词': 'a cat walking on the grass, cinematic',
    '反向提示词': 'bad video',
    '视频宽': 256,
    '视频高': 160,
    '视频时长': 1,
    '输入视频1': '上传/3658c990049f47189d223a75423fa19f.mp4',
    '输入图1': '上传/cfbe2a65406e40e18efdb894eda716b0.jpg',
}

t = task.objects.create(**参数)
print('任务id=%s 类型=%s' % (t.id, 类型))
开始 = time.time()
_跑comfy任务(t.id)
耗时 = time.time() - 开始

t.refresh_from_db()
print('--- 结果 ---')
print('状态   =', t.状态)
print('耗时   = %.1f 秒' % 耗时)
print('产物视频1 =', t.产物视频1)
print('错误信息 =', (t.错误信息 or '')[:600])
