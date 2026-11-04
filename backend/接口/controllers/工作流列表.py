# -*- coding: utf-8 -*-
"""工作流列表控制器：GET 工作流列表。列 backend/资源/工作流/ 下的文件。"""
import datetime
import traceback

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 工作流列表(请求):
    """列出工作流目录下的全部文件。"""
    try:
        目录 = settings.RESOURCE_DIR / '工作流'
        目录.mkdir(parents=True, exist_ok=True)

        列表 = []
        for 项 in sorted(目录.iterdir()):
            if 项.is_file():
                统计 = 项.stat()
                列表.append({
                    '名': 项.name,
                    '大小': 统计.st_size,
                    '修改时间': datetime.datetime.fromtimestamp(统计.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                })
        return Response({'ok': True, '列表': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
