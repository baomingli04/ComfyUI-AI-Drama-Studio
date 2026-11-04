# -*- coding: utf-8 -*-
"""分集保存控制器：POST api/分集/保存。/script/outline 分集目录页落库。

请求体 {剧id, 分集们:[{集号,标题,梗概,钩子,状态,幕,关键,卡点,情绪分,字数,目标,尾钩,中心句,出场,点位}]}：
字段白名单校验 + 按列长截断，事务内全量替换该剧分集（删旧插新，按集号排序）。
多值字段格式：出场=顿号分隔人名；点位=换行分隔、每行「类型｜点｜内容」。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.分集 import 分集
from 接口.返回.错误 import 取错误位置

# 白名单：列名 → 最大长度（None = text 不限）
分集字段 = {
    '标题': 100, '梗概': 500, '钩子': 500, '状态': 10,
    '幕': 50, '尾钩': 500, '中心句': 255, '出场': None, '点位': None,
}
# 整数列（单独处理，防字符串/越界）
分集整数 = {'情绪分': (1, 5), '字数': (0, 1000000), '目标': (0, 1000000)}


def 截断(值, 长):
    文 = '' if 值 is None else str(值)
    if 长 and len(文) > 长:
        return 文[:长]
    return 文


@api_view(['POST'])
def 分集保存(请求):
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

        分集们 = 请求.data.get('分集们')
        if not isinstance(分集们, list):
            return Response({'ok': False, 'error': '分集们必须是数组。'}, status=status.HTTP_400_BAD_REQUEST)

        行们 = []
        见过的集号 = set()
        for 序, 项 in enumerate(分集们):
            if not isinstance(项, dict):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个分集不是对象。'},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                集号 = int(项.get('集号'))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个分集缺少有效集号。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if 集号 < 1:
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个分集集号必须 ≥ 1。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if 集号 in 见过的集号:
                return Response({'ok': False, 'error': '集号 ' + str(集号) + ' 重复。'},
                                status=status.HTTP_400_BAD_REQUEST)
            见过的集号.add(集号)

            行 = {列: 截断(项.get(列), 分集字段[列]) for 列 in 分集字段}
            if not 行['梗概'].strip():
                行['梗概'] = '（待补）'
            if not 行['状态'].strip():
                行['状态'] = '待创作'
            行['关键'] = bool(项.get('关键'))
            行['卡点'] = bool(项.get('卡点'))
            for 列, (下, 上) in 分集整数.items():
                try:
                    值 = int(项.get(列))
                except (TypeError, ValueError):
                    值 = 下
                行[列] = max(下, min(上, 值))
            行们.append({'集号': 集号, **行})

        行们.sort(key=lambda 行: 行['集号'])
        import datetime
        此刻 = datetime.datetime.now()
        with transaction.atomic():
            分集.objects.filter(剧id=剧id).delete()
            for 行 in 行们:
                分集.objects.create(剧id=剧id, 创建时间=此刻, 更新时间=此刻, **行)

        return Response({'ok': True, '剧id': 剧id, '条数': len(行们)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
