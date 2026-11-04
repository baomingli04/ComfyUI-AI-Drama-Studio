# -*- coding: utf-8 -*-
"""资产列表控制器：GET api/资产/列表?剧id=&集号=。/video/assets 资产清单页数据源。

集号可省略：省略时返回该剧全部集的资产（剧集详情页统计 / 全剧资产视图用），
按 集号+排序 升序。归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.返回.错误 import 取错误位置


def 行字典(行):
    return {
        'id': 行.id,
        '剧id': 行.剧id,
        '集号': 行.集号,
        '资产id': 行.资产id or '',
        '类型': 行.类型 or '道具',
        '名称': 行.名称 or '',
        '别名': 行.别名 or '',
        '关系': 行.关系 or '新增',
        '级别': 行.级别 or '',
        '摘要': 行.摘要 or '',
        '排序': 行.排序 or 0,
        '更新时间': 行.更新时间.isoformat() if 行.更新时间 else None,
    }


@api_view(['GET'])
def 资产列表(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        剧id = 请求.GET.get('剧id')
        try:
            剧id = int(剧id)
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        查询 = 资产.objects.filter(剧id=剧id)
        集号 = 请求.GET.get('集号')
        if 集号 not in (None, ''):
            try:
                查询 = 查询.filter(集号=int(集号))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '集号必须是数字。'}, status=status.HTTP_400_BAD_REQUEST)

        行们 = list(查询.order_by('集号', '排序', 'id'))
        列表 = [行字典(行) for 行 in 行们]
        return Response({'ok': True, '剧id': 剧id, '总数': len(列表), '资产们': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
