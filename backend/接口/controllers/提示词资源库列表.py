# -*- coding: utf-8 -*-
"""提示词资源库列表：GET api/提示词资源库/列表?page=1。数据直连 comfyit.cn，不落库。"""
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 能力.提示词资源库 import 每页条数, 取列表
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 提示词资源库列表(请求):
    """返回站点提示词广场第 page 页的图片列表（不含提示词，提示词点开再取详情）。"""
    try:
        try:
            页码 = int(请求.query_params.get('page') or 1)
        except (TypeError, ValueError):
            raise ValueError('页码无效（page 必须是数字）')
        if 页码 < 1:
            raise ValueError('页码无效（从 1 开始）')

        条目列表, 总数 = 取列表(页码)
        return Response({
            'ok': True,
            '页': 页码,
            '每页': 每页条数,
            '总数': 总数,
            '列表': 条目列表,
        })

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
