# -*- coding: utf-8 -*-
"""提示词技能列表：GET api/提示词/技能列表?分类=<分类名>。

列出指定「技能分类.名称」下的技能，且目录下有 SKILL.md。
分类名由前端按页面传：视频类页面默认 `minimax`；图片类页面（T3 生成图片 / T3B 生成图片8K /
三图编辑一致版）传 `图片提示词扩写`。不传时按 `minimax`，保持原有 9 个工作流行为不变。
「技能类型」= 技能分类.名称，技能表没有、也不再加「技能类型」列，所以这里按分类名筛，不按技能名写死。
见 docs/02 3.3 硬规则第 6 条。
"""
import traceback

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 接口.models.技能 import 技能
from 接口.返回.错误 import 取错误位置

# 不传 分类 时的缺省分类名（视频类页面沿用）
缺省分类名 = 'minimax'


@api_view(['GET'])
def 提示词技能列表(请求):
    """列出可用于提示词扩写的技能：按分类名筛，且目录下有 SKILL.md。"""
    try:
        根 = settings.SKILL_DIR
        分类名 = (请求.query_params.get('分类') or '').strip() or 缺省分类名
        列表 = []
        # 硬规则：扩写下拉按分类名筛（不按技能名写死）
        for 一行 in 技能.objects.filter(分类id__名称=分类名).order_by('id'):
            目录 = 根 / 一行.目录名
            if not (目录 / 'SKILL.md').is_file():
                continue
            列表.append({
                'id': 一行.id,
                '名称': 一行.名称,
                '简介': (一行.简介 or '')[:200],
                '目录名': 一行.目录名,
                '分类名称': 分类名,
            })
        return Response({'ok': True, '分类': 分类名, '列表': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
