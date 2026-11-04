# -*- coding: utf-8 -*-
"""资产全部控制器：GET api/资产/全部。/#/assets 资产库页数据源。

返回当前用户全部剧的全部资产行（跨剧汇总），每行带：
剧名、美术定装生图状态、当前参考图列表（按排序，用于卡片缩略图）。
可选 ?类型=人物|场景|道具|服装 过滤（前端也做本地过滤，这里给服务端兜底）。
归属校验：只统计当前登录用户自己的剧。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.models.美术定装 import 美术定装
from 接口.models.参考图 import 参考图
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 资产全部(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        剧行们 = 剧.objects.filter(用户id=请求.user.id)
        剧名表 = {行.id: (行.剧名 or ('剧' + str(行.id))) for 行 in 剧行们}

        类型 = (请求.query_params.get('类型') or '').strip()
        查询 = 资产.objects.filter(剧id__in=list(剧名表.keys()))
        if 类型:
            查询 = 查询.filter(类型=类型)
        行们 = list(查询.order_by('剧id', '集号', '排序', 'id'))

        资产行ids = [行.id for 行 in 行们]

        # 美术定装：资产行id → 生图状态（一资产一定装行）
        状态表 = {}
        if 资产行ids:
            for 定 in 美术定装.objects.filter(资产行id__in=资产行ids):
                状态表[定.资产行id] = 定.生图状态 or '待生成'

        # 当前参考图：资产行id → [{url, 标注}]（按 排序,id 升序）
        图表 = {}
        if 资产行ids:
            for 图 in 参考图.objects.filter(资产行id__in=资产行ids, 状态='当前').order_by('排序', 'id'):
                图表.setdefault(图.资产行id, []).append({'url': 图.url or '', '标注': 图.标注 or ''})

        列表 = [{
            'id': 行.id,
            '剧id': 行.剧id,
            '剧名': 剧名表.get(行.剧id, ''),
            '集号': 行.集号,
            '资产id': 行.资产id or '',
            '类型': 行.类型 or '道具',
            '名称': 行.名称 or '',
            '别名': 行.别名 or '',
            '关系': 行.关系 or '新增',
            '级别': 行.级别 or '',
            '摘要': 行.摘要 or '',
            '生图状态': 状态表.get(行.id, '待生成'),
            '图们': 图表.get(行.id, []),
            '更新时间': 行.更新时间.strftime('%Y-%m-%d %H:%M') if 行.更新时间 else '',
        } for 行 in 行们]

        return Response({'ok': True, '资产们': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
