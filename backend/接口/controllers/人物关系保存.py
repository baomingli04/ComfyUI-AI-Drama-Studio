# -*- coding: utf-8 -*-
"""人物关系保存控制器：POST api/人物/关系保存。/script/character 关系网落库。

请求体 {剧id, 关系们:[{甲,乙,类型,关键词,说明,边序}]}：
字段白名单校验 + 按列长截断，事务内全量替换该剧关系边。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import datetime
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.人物关系 import 人物关系
from 接口.返回.错误 import 取错误位置

# 白名单：列名 → 最大长度（None = text 不限）
关系字段 = {'甲': 50, '乙': 50, '类型': 20, '关键词': 255, '说明': None}


def 截断(值, 长):
    文 = '' if 值 is None else str(值)
    if 长 and len(文) > 长:
        return 文[:长]
    return 文


@api_view(['POST'])
def 人物关系保存(请求):
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

        关系们 = 请求.data.get('关系们')
        if not isinstance(关系们, list):
            return Response({'ok': False, 'error': '关系们必须是数组。'}, status=status.HTTP_400_BAD_REQUEST)

        行们 = []
        for 序, 项 in enumerate(关系们):
            if not isinstance(项, dict):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 条关系不是对象。'},
                                status=status.HTTP_400_BAD_REQUEST)
            甲 = 截断(项.get('甲'), 关系字段['甲']).strip()
            乙 = 截断(项.get('乙'), 关系字段['乙']).strip()
            if not 甲 or not 乙:
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 条关系缺少甲或乙。'},
                                status=status.HTTP_400_BAD_REQUEST)
            行 = {列: 截断(项.get(列), 关系字段[列]) for 列 in 关系字段}
            try:
                行['边序'] = int(项.get('边序') or 序)
            except (TypeError, ValueError):
                行['边序'] = 序
            行们.append(行)

        此刻 = datetime.datetime.now()
        with transaction.atomic():
            人物关系.objects.filter(剧id=剧id).delete()
            for 序, 行 in enumerate(行们):
                人物关系.objects.create(剧id=剧id, 创建时间=此刻, 更新时间=此刻, **行)

        return Response({'ok': True, '剧id': 剧id, '条数': len(行们)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
