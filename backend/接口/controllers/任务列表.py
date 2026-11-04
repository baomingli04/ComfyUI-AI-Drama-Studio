# -*- coding: utf-8 -*-
"""任务列表控制器：GET 任务列表?类型=&条数=50。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置


def _耗时秒(一行):
    """耗时 = 结束时间 - 开始时间（开始时间是交给 ComfyUI 真正开跑的时刻）。

    task 不再单独存耗时，两个时间缺一个就没有耗时。
    """
    if 一行.开始时间 and 一行.结束时间:
        return str(round((一行.结束时间 - 一行.开始时间).total_seconds(), 2))
    return ''


@api_view(['GET'])
def 任务列表(请求):
    """任务列表，可按类型过滤，默认最近 50 条。"""
    try:
        行 = task.objects.order_by('-id')
        类型 = 请求.query_params.get('类型')
        if 类型:
            行 = 行.filter(类型=类型)

        条数 = int(请求.query_params.get('条数') or 50)
        行 = 行[:条数]

        列表 = []
        for 一行 in 行:
            条目 = {
                'id': 一行.id,
                '类型': 一行.类型,
                '状态': 一行.状态,
                '正向提示词': 一行.正向提示词 or '',
                '创建时间': 一行.创建时间.strftime('%Y-%m-%d %H:%M:%S') if 一行.创建时间 else '',
                '开始时间': 一行.开始时间.strftime('%Y-%m-%d %H:%M:%S') if 一行.开始时间 else '',
                '结束时间': 一行.结束时间.strftime('%Y-%m-%d %H:%M:%S') if 一行.结束时间 else '',
                '产物图片': 一行.产物图片 or '',
                '产物图片2': 一行.产物图片2 or '',
                '产物视频1': 一行.产物视频1 or '',
                '产物视频2': 一行.产物视频2 or '',
                '回复': 一行.回复 or '',
                '错误信息': 一行.错误信息 or '',
                '生成时长': _耗时秒(一行),
                'cfg': str(一行.cfg) if 一行.cfg is not None else '',
                '视频宽': 一行.视频宽 if 一行.视频宽 is not None else '',
                '视频高': 一行.视频高 if 一行.视频高 is not None else '',
                '视频时长': str(一行.视频时长) if 一行.视频时长 is not None else '',
                'seed': 一行.seed if 一行.seed is not None else '',
                # 导演台全能：前端「参数」列要显示模式与有声/静音
                '模式': 一行.模式 or '',
                '生成声音': bool(一行.生成声音) if 一行.生成声音 is not None else '',
                '步数': 一行.步数 if 一行.步数 is not None else '',
                '采样器': 一行.采样器 or '',
            }
            # 输入媒体：前端要显示缩略图，不只显示路径
            for i in range(1, 10):
                条目['输入图%d' % i] = getattr(一行, '输入图%d' % i) or ''
            for i in range(1, 4):
                条目['输入视频%d' % i] = getattr(一行, '输入视频%d' % i) or ''
            for i in range(1, 4):
                条目['输入音频%d' % i] = getattr(一行, '输入音频%d' % i) or ''
            列表.append(条目)
        return Response({'ok': True, '列表': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
