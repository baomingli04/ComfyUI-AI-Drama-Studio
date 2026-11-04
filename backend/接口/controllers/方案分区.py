# -*- coding: utf-8 -*-
"""方案分区读取控制器：GET api/方案/分区?方案id=。/script/detail 方案详情页数据源。

返回该方案的五个分区 JSON 内容（时空背景/故事线/爽点矩阵/商业卖点/结局设计），
从未生成过的分区为 null，前端按空结构渲染。
归属校验：方案 → 剧 → 剧的用户id 必须等于当前登录用户。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.方案 import 方案
from 接口.返回.错误 import 取错误位置

分区列 = ('时空背景', '故事线', '爽点矩阵', '商业卖点', '结局设计')


@api_view(['GET'])
def 方案分区(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            方案id = int(请求.query_params.get('方案id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少方案 id。'}, status=status.HTTP_400_BAD_REQUEST)

        一行 = 方案.objects.filter(id=方案id).first()
        if 一行 is None:
            return Response({'ok': False, 'error': '方案不存在。'}, status=status.HTTP_404_NOT_FOUND)

        if not 剧.objects.filter(id=一行.剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '方案不存在或无权查看。'}, status=status.HTTP_404_NOT_FOUND)

        分区 = {}
        for 列 in 分区列:
            分区[列] = getattr(一行, 列)

        return Response({'ok': True, '方案id': 一行.id, '分区': 分区})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
