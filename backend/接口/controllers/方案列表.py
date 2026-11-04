# -*- coding: utf-8 -*-
"""方案列表控制器：GET api/方案列表?剧id=。/script/plan 方案卡数据源（候选卡 JSON）。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.方案 import 方案
from 接口.返回.错误 import 取错误位置


def 方案_to_dict(一行):
    return {
        'id': 一行.id,
        '版本号': 一行.版本号,
        '是否选定': bool(一行.是否选定),
        '候选卡': 一行.候选卡 or {},
        '更新时间': 一行.更新时间.strftime('%Y-%m-%d %H:%M') if 一行.更新时间 else '',
    }


@api_view(['GET'])
def 方案列表(请求):
    """某部剧的全部候选方案，按 id 正序（方案一、方案二…）。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            剧id = int(请求.query_params.get('剧id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权查看。'}, status=status.HTTP_404_NOT_FOUND)

        行 = 方案.objects.filter(剧id=剧id).order_by('id')
        return Response({'ok': True, '列表': [方案_to_dict(一) for 一 in 行]})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
