# -*- coding: utf-8 -*-
"""剧详情控制器：GET api/剧/详情?id=。本人校验；/script/plan 等页实时取 标题/题材/起点方式/创意。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.controllers.剧列表 import 剧_to_dict
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 剧详情(请求):
    """单部剧详情（仅本人可见），字段与 剧列表 完全一致。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            剧id = int(请求.query_params.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        一行 = 剧.objects.filter(id=剧id, 用户id=请求.user.id).first()
        if 一行 is None:
            return Response({'ok': False, 'error': '剧不存在或无权查看。'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'ok': True, '剧': 剧_to_dict(一行)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
