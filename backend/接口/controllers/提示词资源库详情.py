# -*- coding: utf-8 -*-
"""提示词资源库详情：GET api/提示词资源库/详情?id=站点id。返回完整正向/反向提示词。"""
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 能力.提示词资源库 import 取详情
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 提示词资源库详情(请求):
    """按站点 id 取详情：列表接口不给提示词，点开某一条时才拉。"""
    try:
        站点id = 请求.query_params.get('id')
        if not 站点id:
            raise ValueError('id 必填（站点提示词 id）')

        详情 = 取详情(站点id)
        return Response({
            'ok': True,
            '正向提示词': 详情['正向提示词'],
            '反向提示词': 详情['反向提示词'],
            '标题': 详情['标题'],
            '描述': 详情['描述'],
            '封面': 详情['封面'],
        })

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
