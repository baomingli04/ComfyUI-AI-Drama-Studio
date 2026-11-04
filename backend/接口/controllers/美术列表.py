# -*- coding: utf-8 -*-
"""美术列表控制器：GET api/美术/列表?剧id=&集号=。/video/art 美术资产页数据源。

返回该剧（可按集号过滤）全部资产行 + 各自的美术定装行 + 参考图（当前+历史）。
没有定装行的资产行照常返回（定装字段为 null），前端据此提示/自动初始化。
归属校验：剧的用户id 必须等于当前登录用户。
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


def 图字典(行):
    return {
        'id': 行.id,
        '资产行id': 行.资产行id,
        'url': 行.url or '',
        '标注': 行.标注 or '',
        '提示词': 行.提示词 or '',
        '分类': 行.分类 or '',
        '形态': 行.形态 or '',
        '关联人物': 行.关联人物 or '',
        '来源': 行.来源 or '生成',
        '状态': 行.状态 or '当前',
        '排序': 行.排序 or 0,
        '创建时间': 行.创建时间.isoformat() if 行.创建时间 else None,
    }


def 定装字典(行):
    return {
        'id': 行.id,
        '资产行id': 行.资产行id,
        '全局风格': 行.全局风格 or '',
        '画幅': 行.画幅 or '9:16',
        '分辨率': 行.分辨率 or '480p',
        '生图提示词': 行.生图提示词 or '',
        '必须保持': 行.必须保持 or '',
        '禁止出现': 行.禁止出现 or '',
        '生图状态': 行.生图状态 or '待生成',
        '音色提示词': 行.音色提示词 or '',
        '音色名': 行.音色名 or '',
        '音色url': 行.音色url or '',
        '音色模型': 行.音色模型 or '',
        '音色积分': float(行.音色积分) if 行.音色积分 is not None else None,
        '音色状态': 行.音色状态 or '待生成',
        '更新时间': 行.更新时间.isoformat() if 行.更新时间 else None,
    }


@api_view(['GET'])
def 美术列表(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        剧id = 请求.GET.get('剧id')
        try:
            剧id = int(剧id)
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        查询 = 资产.objects.filter(剧id=剧id)
        集号 = 请求.GET.get('集号')
        if 集号 not in (None, ''):
            try:
                查询 = 查询.filter(集号=int(集号))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '集号必须是数字。'}, status=status.HTTP_400_BAD_REQUEST)

        资产行们 = list(查询.order_by('集号', '排序', 'id'))
        资产行ids = [行.id for 行 in 资产行们]

        定装映射 = {}
        if 资产行ids:
            for 定装行 in 美术定装.objects.filter(资产行id__in=资产行ids):
                定装映射[定装行.资产行id] = 定装行

        图映射 = {}
        定装ids = [行.id for 行 in 定装映射.values()]
        if 定装ids:
            for 图行 in 参考图.objects.filter(资产行id__in=定装ids).order_by('排序', 'id'):
                图映射.setdefault(图行.资产行id, []).append(图字典(图行))

        列表 = []
        for 资产行 in 资产行们:
            项 = {
                '资产行id': 资产行.id,
                '剧id': 资产行.剧id,
                '集号': 资产行.集号,
                '资产id': 资产行.资产id or '',
                '类型': 资产行.类型 or '道具',
                '名称': 资产行.名称 or '',
                '别名': 资产行.别名 or '',
                '关系': 资产行.关系 or '新增',
                '级别': 资产行.级别 or '',
                '摘要': 资产行.摘要 or '',
                '定装': None,
                '图们': [],
            }
            定装行 = 定装映射.get(资产行.id)
            if 定装行:
                项['定装'] = 定装字典(定装行)
                项['图们'] = 图映射.get(定装行.id, [])
            列表.append(项)

        统计 = {'人物': 0, '场景': 0, '道具': 0, '服装': 0}
        for 项 in 列表:
            if 项['类型'] in 统计:
                统计[项['类型']] += 1

        return Response({'ok': True, '剧id': 剧id, '总数': len(列表),
                         '统计': 统计, '行们': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
