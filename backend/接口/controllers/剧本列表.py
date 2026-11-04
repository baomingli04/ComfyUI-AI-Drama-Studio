# -*- coding: utf-8 -*-
"""剧本列表控制器：GET api/剧本/列表?剧id=。/script/episode 分集剧本页数据源。

返回该剧 版本类型=创作版、版本=1 的剧本行们（按集号升序），每行带 场次们（按 排序 升序）。
场次来自 `场次` 实体表（docs 02 第 12 节）；`剧本.场次` json 列已弃用不再读。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.剧本 import 剧本
from 接口.models.场次 import 场次
from 接口.返回.错误 import 取错误位置


def 行字典(行, 场们):
    return {
        'id': 行.id,
        '剧id': 行.剧id,
        '集号': 行.集号,
        '版本类型': 行.版本类型,
        '版本': 行.版本,
        '标题': 行.标题 or '',
        '总字数': 行.总字数 or 0,
        '正文': 行.正文 or '',
        '能力档案': 行.能力档案 or '',
        '世界状态': 行.世界状态 or '',
        '关系网络': 行.关系网络 or '',
        '记忆回廊': 行.记忆回廊 or '',
        '行动推荐': 行.行动推荐 or '',
        '状态': 行.状态 or '待复核',
        '定稿': bool(行.定稿),
        '定稿时间': 行.定稿时间.isoformat() if 行.定稿时间 else None,
        '创建时间': 行.创建时间.isoformat() if 行.创建时间 else None,
        '更新时间': 行.更新时间.isoformat() if 行.更新时间 else None,
        '场次们': 场们,
    }


@api_view(['GET'])
def 剧本列表(请求):
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

        行们 = list(剧本.objects.filter(剧id=剧id, 版本类型='创作版', 版本=1).order_by('集号'))
        行id们 = [行.id for 行 in 行们]
        # 一次查出全部场次，按剧本行分组
        场分组 = {}
        if 行id们:
            for 场 in 场次.objects.filter(剧本行id__in=行id们).order_by('排序', 'id'):
                场分组.setdefault(场.剧本行id, []).append({
                    '场': 场.场号 or '',
                    '地点': 场.地点 or '',
                    '人物': 场.人物 or '',
                    '道具': 场.道具 or '',
                    '正文': (场.正文 or '').split('\n') if 场.正文 else [],
                    '排序': 场.排序 or 0,
                })

        列表 = [行字典(行, 场分组.get(行.id, [])) for 行 in 行们]
        return Response({'ok': True, '剧id': 剧id, '总数': len(列表), '剧本们': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
