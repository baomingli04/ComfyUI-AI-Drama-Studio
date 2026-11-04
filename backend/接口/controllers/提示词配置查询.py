# -*- coding: utf-8 -*-
"""提示词配置查询：GET api/提示词/配置?类型=xxx。

按 类型 取 提示词模板 的一行，返回 内容（= 系统提示词 列原文，不加工）。
扩写场景类型形如 `扩写:/test/d7-refine`，见 docs/02 第 8 节。
取不到行时返回空内容，由前端填默认规则。
"""
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 接口.models.提示词模板 import 提示词模板
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 提示词配置查询(请求):
    """按类型取提示词配置；没有则返回空内容。"""
    try:
        类型 = (请求.query_params.get('类型') or '').strip()
        if not 类型:
            raise ValueError('类型不能为空')

        实例 = 提示词模板.objects.filter(类型=类型).first()
        return Response({
            'ok': True,
            '类型': 类型,
            '内容': (实例.系统提示词 if 实例 and 实例.系统提示词 else '') if 实例 else '',
        })

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
