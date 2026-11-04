# -*- coding: utf-8 -*-
"""音频信息控制器：POST api/音频/信息。

同步接口：读音频/视频的 时长/采样率/声道（只探测，不产出文件）。
body: { 路径 }
返回 { ok, 时长, 采样率, 声道 }
"""
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 能力.音频剪辑 import 取音频信息
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 音频信息(请求):
    try:
        数据 = 请求.data or {}
        路径 = (数据.get('路径') or '').strip()
        if not 路径:
            return Response({'ok': False, 'error': '缺少 路径。'},
                            status=status.HTTP_400_BAD_REQUEST)

        结果 = 取音频信息(路径)
        return Response({'ok': True, '时长': 结果['时长'],
                         '采样率': 结果['采样率'], '声道': 结果['声道']})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
