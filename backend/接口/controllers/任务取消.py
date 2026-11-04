# -*- coding: utf-8 -*-
"""任务取消控制器：POST 任务/取消。排队中的直接取消，生成中的标记后由执行器 interrupt。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 任务取消(请求):
    """取消单个任务：已创建/已提交/排队中/生成中 均可取消。"""
    try:
        任务id = 请求.data.get('id')
        if not 任务id:
            return Response(
                {'ok': False, 'error': '缺少任务 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            实例 = task.objects.get(id=int(任务id))
        except task.DoesNotExist:
            return Response(
                {'ok': False, 'error': '任务不存在：' + str(任务id)},
                status=status.HTTP_404_NOT_FOUND,
            )

        from 能力.提交并等待 import 标记取消接口入口
        if not 标记取消接口入口(实例):
            return Response(
                {'ok': False, 'error': '当前状态不可取消：' + 实例.状态},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'ok': True, '状态': '已取消'})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
