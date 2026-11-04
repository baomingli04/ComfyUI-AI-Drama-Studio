# -*- coding: utf-8 -*-
"""任务状态控制器：GET 任务/状态?id= → 轻量返回单个任务的状态与产物。

给前端轮询用（成片合成、音色合成等后台任务），比拉全量任务列表省。
只允许查自己创建的任务。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 任务状态(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)
        try:
            任务id = int(请求.query_params.get('id') or 0)
        except (TypeError, ValueError):
            任务id = 0
        if not 任务id:
            return Response({'ok': False, 'error': '缺少任务 id。'},
                            status=status.HTTP_400_BAD_REQUEST)
        任务 = task.objects.filter(id=任务id).first()
        if 任务 is None or 任务.创建人id_id != 请求.user.id:
            return Response({'ok': False, 'error': '任务不存在。'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({
            'ok': True,
            'id': 任务.id,
            '类型': 任务.类型,
            '状态': 任务.状态,
            '错误信息': 任务.错误信息 or '',
            '产物图片': 任务.产物图片 or '',
            '产物视频1': 任务.产物视频1 or '',
            '回复': 任务.回复 or '',
        })
    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
