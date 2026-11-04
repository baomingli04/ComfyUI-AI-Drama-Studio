# -*- coding: utf-8 -*-
"""工作流下载控制器：GET 工作流/下载?名=xxx.json。"""
import traceback

from django.conf import settings
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 工作流下载(请求):
    """下载工作流目录里的单个文件（attachment）。"""
    try:
        名 = 请求.query_params.get('名') or ''
        if not 名 or '/' in 名 or '\\' in 名 or '..' in 名:
            return Response(
                {'ok': False, 'error': '非法文件名。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        目标 = settings.RESOURCE_DIR / '工作流' / 名
        if not 目标.is_file():
            return Response(
                {'ok': False, 'error': '文件不存在：' + 名},
                status=status.HTTP_404_NOT_FOUND,
            )

        响应 = FileResponse(open(目标, 'rb'))
        响应['Content-Disposition'] = 'attachment; filename="' + 名.encode('ascii', 'ignore').decode() + '"'
        响应['X-真实文件名'] = 名
        return 响应

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
