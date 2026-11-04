# -*- coding: utf-8 -*-
"""资产保存控制器：POST api/资产/保存。/video/assets 资产清单页落库。

请求体 {剧id, 集号, 项们:[{资产id, 类型, 名称, 别名(顿号分隔文本), 关系, 级别, 摘要}]}：
字段白名单校验 + 按列长截断；事务内全量替换该剧该集的资产行（按传参顺序写 排序）。
项们 传空数组 = 清空该集资产。类型必须是 人物/场景/道具/服装 之一。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import datetime
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.返回.错误 import 取错误位置

# 白名单：列名 → 最大长度（None = text 不限）
资产字段 = {
    '资产id': 32, '类型': 10, '名称': 100, '别名': 300,
    '关系': 10, '级别': 50, '摘要': None,
}
类型们 = ('人物', '场景', '道具', '服装')
关系们 = ('新增', '引用')


def 截断(值, 长):
    文 = '' if 值 is None else str(值)
    if 长 and len(文) > 长:
        return 文[:长]
    return 文


@api_view(['POST'])
def 资产保存(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        剧id = 请求.data.get('剧id')
        try:
            剧id = int(剧id)
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        try:
            集号 = int(请求.data.get('集号'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少有效集号。'}, status=status.HTTP_400_BAD_REQUEST)
        if 集号 < 1:
            return Response({'ok': False, 'error': '集号必须 ≥ 1。'}, status=status.HTTP_400_BAD_REQUEST)

        项们 = 请求.data.get('项们')
        if not isinstance(项们, list):
            return Response({'ok': False, 'error': '项们必须是数组。'}, status=status.HTTP_400_BAD_REQUEST)

        准备们 = []
        见过的资产id = set()
        for 序, 项 in enumerate(项们):
            if not isinstance(项, dict):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 项不是对象。'},
                                status=status.HTTP_400_BAD_REQUEST)
            行 = {列: 截断(项.get(列), 资产字段[列]) for 列 in 资产字段}
            if not 行['资产id'].strip():
                前缀 = {'人物': 'CHAR', '场景': 'SCN', '道具': 'PROP', '服装': 'COST'}.get(行['类型'], 'PROP')
                行['资产id'] = '%s_%03d' % (前缀, 序 + 1)
            if 行['资产id'] in 见过的资产id:
                return Response({'ok': False, 'error': '资产id ' + 行['资产id'] + ' 重复。'},
                                status=status.HTTP_400_BAD_REQUEST)
            见过的资产id.add(行['资产id'])
            if 行['类型'] not in 类型们:
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 项类型必须是 ' + '、'.join(类型们) + '。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not 行['名称'].strip():
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 项缺少名称。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if 行['关系'] not in 关系们:
                行['关系'] = '新增'
            行['排序'] = 序
            准备们.append(行)

        此刻 = datetime.datetime.now()
        with transaction.atomic():
            资产.objects.filter(剧id=剧id, 集号=集号).delete()
            for 行 in 准备们:
                资产.objects.create(剧id=剧id, 集号=集号, 创建时间=此刻, 更新时间=此刻, **行)

        return Response({'ok': True, '剧id': 剧id, '集号': 集号, '项数': len(准备们)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
