# -*- coding: utf-8 -*-
"""分集列表控制器：GET api/分集/列表?剧id=。/script/outline 分集目录页读库回显。

按 集号 升序回该剧全部分集行（含 2026-11-02 扩的 10 列）。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分集 import 分集
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 分集列表(请求):
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

        行们 = 分集.objects.filter(剧id=剧id).order_by('集号')
        分集们 = []
        for 行 in 行们:
            分集们.append({
                'id': 行.id,
                '集号': 行.集号,
                '标题': 行.标题 or '',
                '梗概': 行.梗概 or '',
                '钩子': 行.钩子 or '',
                '状态': 行.状态 or '待创作',
                '幕': 行.幕 or '',
                '关键': bool(行.关键),
                '卡点': bool(行.卡点),
                '情绪分': 行.情绪分 if 行.情绪分 is not None else 3,
                '字数': 行.字数 or 0,
                '目标': 行.目标 or 3000,
                '尾钩': 行.尾钩 or '',
                '中心句': 行.中心句 or '',
                '出场': 行.出场 or '',
                '点位': 行.点位 or '',
            })
        return Response({'ok': True, '分集们': 分集们, '总数': len(分集们)})
    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
