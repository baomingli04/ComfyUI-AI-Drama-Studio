# -*- coding: utf-8 -*-
"""剧列表控制器：GET 剧列表。只返回当前登录用户的剧（§9.3 隔离）。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.返回.错误 import 取错误位置


def 剧_to_dict(一行):
    """统一序列化：前端列表卡与详情页共用。"""
    return {
        'id': 一行.id,
        '剧名': 一行.剧名,
        '集数': 一行.集数,
        '题材': 一行.题材,
        '创意': 一行.创意,
        '起点方式': 一行.起点方式,
        '封面图片': 一行.封面图片 or '',
        '保存地址': 一行.保存地址 or '',
        '状态': 一行.状态,
        '创作进度': 一行.创作进度,
        '视频进度': 一行.视频进度,
        '创建时间': 一行.创建时间.strftime('%Y-%m-%d %H:%M') if 一行.创建时间 else '',
        '更新时间': 一行.更新时间.strftime('%Y-%m-%d %H:%M') if 一行.更新时间 else '',
    }


@api_view(['GET'])
def 剧列表(请求):
    """当前用户的剧全量列表，按 更新时间 倒序。可选 ?关键词= 服务端过滤。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        行 = 剧.objects.filter(用户id=请求.user.id).order_by('-更新时间', '-id')
        关键词 = (请求.query_params.get('关键词') or '').strip()
        if 关键词:
            行 = 行.filter(剧名__icontains=关键词) | 行.filter(题材__icontains=关键词)
        return Response({'ok': True, '列表': [剧_to_dict(一) for 一 in 行]})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
