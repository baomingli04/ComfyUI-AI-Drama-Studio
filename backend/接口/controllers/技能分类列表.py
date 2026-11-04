# -*- coding: utf-8 -*-
"""技能分类列表控制器：GET 技能分类。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.技能分类 import 技能分类
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 技能分类列表(请求):
    """技能分类全量列表，按 排序, id 排。"""
    try:
        行 = 技能分类.objects.order_by('排序', 'id')
        列表 = [
            {
                'id': 一行.id,
                '名称': 一行.名称,
                '编码': 一行.编码,
                '排序': 一行.排序,
                '系统内置': 一行.系统内置,
            }
            for 一行 in 行
        ]
        return Response({'ok': True, '列表': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
