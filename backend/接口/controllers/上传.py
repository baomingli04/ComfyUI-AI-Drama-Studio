# -*- coding: utf-8 -*-
"""上传控制器：POST 上传（multipart，字段名 文件）。存 backend/资源/上传/。"""
import traceback
import uuid

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.返回.错误 import 取错误位置

允许后缀 = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp',
            '.mp4', '.avi', '.mov', '.webm',
            '.mp3', '.wav', '.flac', '.m4a']


@api_view(['POST'])
def 上传(请求):
    """上传单个媒体文件，返回相对路径（存入 task 的 输入图/视频/音频 列）。"""
    try:
        文件 = 请求.FILES.get('文件')
        if 文件 is None:
            return Response(
                {'ok': False, 'error': '没有收到文件（字段名必须是 文件）。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        后缀 = ''
        原名 = 文件.name or ''
        点位 = 原名.rfind('.')
        if 点位 >= 0:
            后缀 = 原名[点位:].lower()
        if 后缀 not in 允许后缀:
            return Response(
                {'ok': False, 'error': '不允许的文件类型：' + 后缀},
                status=status.HTTP_400_BAD_REQUEST,
            )

        上传目录 = settings.UPLOAD_DIR
        上传目录.mkdir(parents=True, exist_ok=True)

        新名 = uuid.uuid4().hex + 后缀
        目标 = 上传目录 / 新名
        with open(目标, 'wb') as f:
            for 块 in 文件.chunks():
                f.write(块)

        return Response({'ok': True, '路径': '上传/' + 新名, '原名': 原名})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
