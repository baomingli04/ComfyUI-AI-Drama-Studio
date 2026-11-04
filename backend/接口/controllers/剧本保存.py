# -*- coding: utf-8 -*-
"""剧本保存控制器：POST api/剧本/保存。/script/episode 分集剧本页落库。

请求体 {剧id, 集们:[{集号, 标题, 正文, 能力档案, 世界状态, 关系网络, 记忆回廊,
行动推荐, 状态, 场们:[{场, 地点, 人物, 道具, 正文(行数组)}]}]}：
字段白名单校验 + 按列长截断；逐集 upsert 创作版 v1 行（标题/总字数/正文/档案/状态），
事务内全量替换该剧集的 `场次` 实体表行（按 排序 删旧插新）；总字数后端按正文去空白重算。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import datetime
import re
import traceback

from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.剧本 import 剧本
from 接口.models.场次 import 场次
from 接口.返回.错误 import 取错误位置

# 白名单：列名 → 最大长度（None = text 不限）
剧本字段 = {
    '标题': 100, '正文': None, '能力档案': None, '世界状态': None,
    '关系网络': None, '记忆回廊': None, '行动推荐': None, '状态': 16,
}


def 截断(值, 长):
    文 = '' if 值 is None else str(值)
    if 长 and len(文) > 长:
        return 文[:长]
    return 文


def 数总字数(正文):
    """总字数口径：去掉空白字符后的正文长度。"""
    return len(re.sub(r'\s', '', str(正文 or '')))


@api_view(['POST'])
def 剧本保存(请求):
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

        集们 = 请求.data.get('集们')
        if not isinstance(集们, list):
            return Response({'ok': False, 'error': '集们必须是数组。'}, status=status.HTTP_400_BAD_REQUEST)

        准备们 = []
        见过的集号 = set()
        for 序, 集 in enumerate(集们):
            if not isinstance(集, dict):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个集不是对象。'},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                集号 = int(集.get('集号'))
            except (TypeError, ValueError):
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个集缺少有效集号。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if 集号 < 1:
                return Response({'ok': False, 'error': '第 ' + str(序 + 1) + ' 个集集号必须 ≥ 1。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if 集号 in 见过的集号:
                return Response({'ok': False, 'error': '集号 ' + str(集号) + ' 重复。'},
                                status=status.HTTP_400_BAD_REQUEST)
            见过的集号.add(集号)

            行 = {列: 截断(集.get(列), 剧本字段[列]) for 列 in 剧本字段}
            if not 行['状态'].strip():
                行['状态'] = '待复核'

            # 场次：正文行数组或换行文本都认，统一成换行文本
            场们 = 集.get('场们')
            场行们 = []
            if isinstance(场们, list):
                for 场序, 场 in enumerate(场们):
                    if not isinstance(场, dict):
                        continue
                    场号 = 截断(场.get('场'), 16).strip()
                    if not 场号:
                        continue
                    正文值 = 场.get('正文')
                    if isinstance(正文值, list):
                        正文文本 = '\n'.join(str(行文) for 行文 in 正文值)
                    else:
                        正文文本 = '' if 正文值 is None else str(正文值)
                    场行们.append({
                        '场号': 场号,
                        '地点': 截断(场.get('地点'), 100),
                        '人物': 截断(场.get('人物'), 200),
                        '道具': 截断(场.get('道具'), 200),
                        '正文': 正文文本[:50000],
                        '排序': 场序,
                    })

            准备们.append({'集号': 集号, '行': 行, '场们': 场行们})

        此刻 = datetime.datetime.now()
        with transaction.atomic():
            for 项 in 准备们:
                行, 新 = 剧本.objects.get_or_create(
                    剧id=剧id, 集号=项['集号'], 版本类型='创作版', 版本=1,
                    defaults={'创建时间': 此刻, '更新时间': 此刻})
                for 列, 值 in 项['行'].items():
                    setattr(行, 列, 值)
                行.总字数 = 数总字数(行.正文)
                行.更新时间 = 此刻
                行.save()
                场次.objects.filter(剧本行id=行.id).delete()
                for 场 in 项['场们']:
                    场次.objects.create(剧id=剧id, 剧本行id=行.id,
                                        创建时间=此刻, 更新时间=此刻, **场)
            # 全量替换语义：删掉本次没传的创作版 v1 行及其场次（定稿版不动）
            传了的集号 = [项['集号'] for 项 in 准备们]
            多余们 = list(剧本.objects.filter(剧id=剧id, 版本类型='创作版', 版本=1)
                        .exclude(集号__in=传了的集号))
            if 多余们:
                多余id们 = [行.id for 行 in 多余们]
                场次.objects.filter(剧本行id__in=多余id们).delete()
                剧本.objects.filter(id__in=多余id们).delete()

        return Response({'ok': True, '剧id': 剧id, '集数': len(准备们)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
