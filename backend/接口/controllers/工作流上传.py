# -*- coding: utf-8 -*-
"""工作流上传控制器：POST 工作流/上传。存 backend/资源/工作流/。"""
import traceback

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.返回.错误 import 取错误位置

允许后缀 = ['.json', '.zip']


@api_view(['POST'])
def 工作流上传(请求):
    """上传工作流文件（json / zip），存到 资源/工作流/，同名覆盖。"""
    try:
        文件 = 请求.FILES.get('文件')
        if 文件 is None:
            return Response(
                {'ok': False, 'error': '没有收到文件（字段名必须是 文件）。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        原名 = 文件.name or ''
        点位 = 原名.rfind('.')
        后缀 = 原名[点位:].lower() if 点位 >= 0 else ''
        if 后缀 not in 允许后缀:
            return Response(
                {'ok': False, 'error': '只允许 json / zip 文件。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        工作流目录 = settings.RESOURCE_DIR / '工作流'
        工作流目录.mkdir(parents=True, exist_ok=True)

        with open(工作流目录 / 原名, 'wb') as f:
            for 块 in 文件.chunks():
                f.write(块)

        return Response({'ok': True, '名': 原名})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
