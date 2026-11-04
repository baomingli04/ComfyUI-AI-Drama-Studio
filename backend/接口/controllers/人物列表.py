# -*- coding: utf-8 -*-
"""人物列表控制器：GET api/人物/列表?剧id=。/script/character 人物设定页数据源。

一次回该剧全部人物卡与关系网边（人物们 + 关系们），空剧回两个空数组。
归属校验：剧的用户id 必须等于当前登录用户。
"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.人物 import 人物
from 接口.models.人物关系 import 人物关系
from 接口.返回.错误 import 取错误位置

人物列 = (
    'id', '人物id', '名', '性别', '年龄档', '性格', '关系',
    '简介', '分组', '卡色',
    '身份', '关系变化', '态度', '外貌', '身材', '穿搭',
    '身体情况', '情感情况', '精神情况', '当前状态', '当前姿势', '内心想法',
    '技能', '核心目标', '关系网', '背景故事', '台词风格', '口头禅', '概括',
)

关系列 = ('id', '甲', '乙', '类型', '关键词', '说明', '边序')


@api_view(['GET'])
def 人物列表(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            剧id = int(请求.query_params.get('剧id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        if not 剧.objects.filter(id=剧id, 用户id=请求.user.id).exists():
            return Response({'ok': False, 'error': '剧不存在或无权查看。'}, status=status.HTTP_404_NOT_FOUND)

        人物们 = []
        for 行 in 人物.objects.filter(剧id=剧id):
            人物们.append({列: getattr(行, 列) for 列 in 人物列})

        关系们 = []
        for 行 in 人物关系.objects.filter(剧id=剧id):
            关系们.append({列: getattr(行, 列) for 列 in 关系列})

        return Response({'ok': True, '剧id': 剧id, '人物们': 人物们, '关系们': 关系们})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
