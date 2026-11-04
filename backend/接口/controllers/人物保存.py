# -*- coding: utf-8 -*-
"""人物保存控制器：POST api/人物/保存。/script/character 人物设定页落库。

请求体 {剧id, 人物们:[{人物id,名,性别,年龄档,性格,关系,简介,…,概括}]}：
字段白名单校验 + 按列长截断，事务内全量替换该剧人物（删旧插新，顺序即页面顺序）。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.人物 import 人物
from 接口.返回.错误 import 取错误位置

# 白名单：列名 → 最大长度（None = text 不限）
人物字段 = {
    '人物id': 32, '名': 50, '性别': 10, '年龄档': 20,
    '性格': None, '关系': None,
    '简介': 255, '分组': 50, '卡色': 10,
    '身份': None, '关系变化': None, '态度': None, '外貌': None, '身材': 255, '穿搭': None,
    '身体情况': None, '情感情况': None, '精神情况': None, '当前状态': None, '当前姿势': 255, '内心想法': None,
    '技能': None, '核心目标': None, '关系网': None, '背景故事': None,
    '台词风格': 255, '口头禅': 255, '概括': 500,
}


def 截断(值, 长):
    文 = '' if 值 is None else str(值)
    if 长 and len(文) > 长:
        return 文[:长]
    return 文


@api_view(['POST'])
def 人物保存(请求):
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

        人物们 = 请求.data.get('人物们')
        if not isinstance(人物们, list):
            return Response({'ok': False, 'error': '人物们必须是数组。'}, status=status.HTTP_400_BAD_REQUEST)

        行们 = []
        for 序, 项 in enumerate(人物们):
            if not isinstance(项, dict):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个人物不是对象。'},
                                status=status.HTTP_400_BAD_REQUEST)
            名 = 截断(项.get('名'), 人物字段['名']).strip()
            if not 名:
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个人物缺少名。'},
                                status=status.HTTP_400_BAD_REQUEST)
            编号 = 截断(项.get('人物id'), 人物字段['人物id']).strip() or ('CHAR_' + str(序 + 1).zfill(3))
            行们.append({列: 截断(项.get(列), 人物字段[列]) for 列 in 人物字段} | {'人物id': 编号, '名': 名})

        import datetime
        此刻 = datetime.datetime.now()
        with transaction.atomic():
            人物.objects.filter(剧id=剧id).delete()
            for 行 in 行们:
                人物.objects.create(剧id=剧id, 创建时间=此刻, 更新时间=此刻, **行)

        return Response({'ok': True, '剧id': 剧id, '条数': len(行们)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
