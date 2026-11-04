# -*- coding: utf-8 -*-
"""视频剧列表控制器：GET api/视频/剧列表。

视频线首页只列「剧本创作里已经生成过分集剧本」的剧：
即 剧本 表里存在 创作版 v1 且 正文 非空 行的剧。
每行带 已生成集数 / 已复核集数 统计，供 /video 卡片直接展示。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.剧本 import 剧本
from 接口.controllers.剧列表 import 剧_to_dict
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 视频剧列表(请求):
    """列出有分集剧本的剧（本人），按 更新时间 倒序。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # 统计每个剧的分集剧本：已生成（有正文的创作版 v1 去重集号）、已复核
        行们 = (
            剧本.objects
            .filter(版本类型='创作版', 版本=1)
            .exclude(正文=None)
            .exclude(正文='')
            .values_list('剧id', '集号', '状态')
        )
        统计 = {}
        for 剧id, 集号, 剧本状态 in 行们:
            项 = 统计.setdefault(剧id, {'集们': set(), '复核': 0})
            项['集们'].add(集号)
            if 剧本状态 == '已复核':
                项['复核'] += 1

        if not 统计:
            return Response({'ok': True, '列表': []})

        剧行们 = 剧.objects.filter(
            id__in=统计.keys(), 用户id=请求.user.id
        ).order_by('-更新时间', '-id')

        列表 = []
        for 一行 in 剧行们:
            项 = 统计[一行.id]
            字典 = 剧_to_dict(一行)
            字典['已生成集数'] = len(项['集们'])
            字典['已复核集数'] = 项['复核']
            列表.append(字典)
        return Response({'ok': True, '列表': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
