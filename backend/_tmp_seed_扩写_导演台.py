# -*- coding: utf-8 -*-
"""把导演台全能六模式的扩写规则写进 提示词模板 表（扩写:/test/d-all:<模式>）。

规则文本的唯一来源是前端的 扩写规则.json —— 本脚本读它写库，前端读它当兜底默认值，
两边不会漂移。已存在的行默认不覆盖（保护用户在页面里改过的内容），要覆盖加 --覆盖。

模式列表直接取 JSON 的 规则 键，不再写死 —— 写死过三模式，加 i2v/v2v/rv2v 时漏过一次。

用法：
    ./.venv/Scripts/python.exe _tmp_seed_扩写_导演台.py
    ./.venv/Scripts/python.exe _tmp_seed_扩写_导演台.py --覆盖
"""
import json
import os
import sys

import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '后端.settings')
django.setup()

from django.utils import timezone  # noqa: E402

from 接口.models.提示词模板 import 提示词模板  # noqa: E402

路由 = '/test/d-all'
JSON路径 = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'frontend', 'src', 'views', '测试', '导演台全能', '扩写规则.json')

覆盖 = '--覆盖' in sys.argv

with open(JSON路径, 'r', encoding='utf-8') as f:
    规则包 = json.load(f)

规则表 = 规则包['规则']
模式说明 = 规则包['模式说明']

for 模式 in 规则表.keys():
    类型 = '扩写:%s:%s' % (路由, 模式)
    内容 = '\n'.join(规则表[模式])
    现在 = timezone.now()
    实例 = 提示词模板.objects.filter(类型=类型).first()
    if 实例 is None:
        提示词模板.objects.create(类型=类型, 系统提示词=内容, 创建时间=现在, 更新时间=现在)
        print('[新增] %s  %d 字  （%s）' % (类型, len(内容), 模式说明[模式][:20] + '…'))
    elif 覆盖:
        实例.系统提示词 = 内容
        实例.更新时间 = 现在
        实例.save(update_fields=['系统提示词', '更新时间'])
        print('[覆盖] %s  %d 字' % (类型, len(内容)))
    else:
        旧 = 实例.系统提示词 or ''
        print('[跳过] %s  库里已有 %d 字%s' % (类型, len(旧), '' if 旧 == 内容 else '（与 JSON 不一致，要覆盖加 --覆盖）'))

print('\n---- 当前所有 扩写: 行 ----')
for 行 in 提示词模板.objects.filter(类型__startswith='扩写:').order_by('类型'):
    print('%-32s %5d 字' % (行.类型, len(行.系统提示词 or '')))
