# -*- coding: utf-8 -*-
"""任务日志控制器：GET 任务/日志?id=。"""
import traceback
from pathlib import Path

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置


def _读日志文件(路径):
    if not 路径:
        return None
    try:
        p = Path(路径)
        if not p.is_file():
            return None
        with open(p, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return None


@api_view(['GET'])
def 任务日志(请求):
    """返回单个任务的运行日志文本（日志文件在 backend/资源/日志/）。"""
    try:
        任务id = 请求.query_params.get('id')
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

        # 优先按任务 id 读标准路径（记日志始终写这里）；库字段为空时也能出日志。
        标准路径 = Path(settings.LOG_DIR) / ('task_%s.log' % 实例.id)
        日志文本 = _读日志文件(标准路径)
        if 日志文本 is None:
            日志文本 = _读日志文件(实例.日志路径)
        if 日志文本 is None:
            日志文本 = ''

        return Response({'ok': True, '日志': 日志文本, '状态': 实例.状态})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
