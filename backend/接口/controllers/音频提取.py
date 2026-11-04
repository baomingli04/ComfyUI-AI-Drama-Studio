# -*- coding: utf-8 -*-
"""音频提取控制器：POST api/音频/提取。

同步接口（本地 ffmpeg，秒级返回），不进任务队列、不落 task 表。
body: { 视频路径, 格式: wav|mp3, 采样率: 0|44100|48000 }
返回 { ok, 路径, 时长, 采样率, 声道 }
"""
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 能力.音频剪辑 import 提取音频
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 音频提取(请求):
    try:
        数据 = 请求.data or {}
        视频路径 = (数据.get('视频路径') or '').strip()
        if not 视频路径:
            return Response({'ok': False, 'error': '缺少 视频路径。'},
                            status=status.HTTP_400_BAD_REQUEST)

        格式 = (数据.get('格式') or 'wav').strip().lower()
        if 格式 not in ('wav', 'mp3'):
            return Response({'ok': False, 'error': '格式只支持 wav / mp3。'},
                            status=status.HTTP_400_BAD_REQUEST)

        采样率 = 数据.get('采样率') or 0
        try:
            采样率 = int(采样率)
        except Exception:
            return Response({'ok': False, 'error': '采样率必须是数字（0 = 保持原样）。'},
                            status=status.HTTP_400_BAD_REQUEST)

        结果 = 提取音频(视频路径, 格式, 采样率)
        return Response({'ok': True, '路径': 结果['路径'], '时长': 结果['时长'],
                         '采样率': 结果['采样率'], '声道': 结果['声道']})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
