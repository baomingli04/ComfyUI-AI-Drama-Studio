# -*- coding: utf-8 -*-
"""分镜列表控制器：GET api/分镜/列表?剧id=&集号=。/video/shot 拆分分镜页数据源。

集号可省略：省略时返回该剧全部集的分镜（剧集详情页统计用），按 集号+排序 升序。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分镜 import 分镜
from 接口.返回.错误 import 取错误位置


def 行字典(行):
    return {
        'id': 行.id,
        '剧id': 行.剧id,
        '集号': 行.集号,
        '镜号': 行.镜号 or '',
        '场次': 行.场次 or '',
        '景别': 行.景别 or '',
        '运镜': 行.运镜 or '',
        '画面': 行.画面 or '',
        '台词': 行.台词 or '',
        '时长': 行.时长 or '',
        '视频状态': 行.视频状态 or '待生成',
        '生成方式': 行.生成方式 or '',
        '生成提示词': 行.生成提示词 or '',
        '排序': 行.排序 or 0,
        '更新时间': 行.更新时间.isoformat() if 行.更新时间 else None,
    }


@api_view(['GET'])
def 分镜列表(请求):
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

        查询 = 分镜.objects.filter(剧id=剧id)
        集号 = 请求.GET.get('集号')
        if 集号 not in (None, ''):
            try:
                查询 = 查询.filter(集号=int(集号))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '集号必须是数字。'}, status=status.HTTP_400_BAD_REQUEST)

        行们 = list(查询.order_by('集号', '排序', 'id'))
        列表 = [行字典(行) for 行 in 行们]
        return Response({'ok': True, '剧id': 剧id, '总数': len(列表), '分镜们': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
