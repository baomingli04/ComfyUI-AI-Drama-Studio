# -*- coding: utf-8 -*-
"""音频合成控制器：POST api/音频/合成。

同步接口（本地 ffmpeg），不进任务队列、不落 task 表。
body: { 源路径, 片段列表: [{开始, 结束}, ...], 模式: 合并|分别, 格式: wav|mp3 }
返回：模式=合并 → { ok, 路径, 时长 }；模式=分别 → { ok, 路径列表 }
"""
import traceback

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 能力.音频剪辑 import 合成音频
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 音频合成(请求):
    try:
        数据 = 请求.data or {}
        源路径 = (数据.get('源路径') or '').strip()
        if not 源路径:
            return Response({'ok': False, 'error': '缺少 源路径。'},
                            status=status.HTTP_400_BAD_REQUEST)

        片段列表 = 数据.get('片段列表') or []
        if not isinstance(片段列表, list) or not 片段列表:
            return Response({'ok': False, 'error': '片段列表为空。'},
                            status=status.HTTP_400_BAD_REQUEST)

        模式 = (数据.get('模式') or '合并').strip()
        if 模式 not in ('合并', '分别'):
            return Response({'ok': False, 'error': '模式只支持 合并 / 分别。'},
                            status=status.HTTP_400_BAD_REQUEST)

        格式 = (数据.get('格式') or 'wav').strip().lower()
        if 格式 not in ('wav', 'mp3'):
            return Response({'ok': False, 'error': '格式只支持 wav / mp3。'},
                            status=status.HTTP_400_BAD_REQUEST)

        结果 = 合成音频(源路径, 片段列表, 模式, 格式)
        if 模式 == '合并':
            return Response({'ok': True, '路径': 结果['路径'], '时长': 结果['时长']})
        return Response({'ok': True, '路径列表': 结果['路径列表']})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
