# -*- coding: utf-8 -*-
"""标签列表控制器：GET api/标签。题材标签库全量（系统内置 + 用户自建），按 排序,id。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.标签 import 标签
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 标签列表(请求):
    """全部题材标签。/script/new 的 chips 与手动添加下拉都从这里读。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        行 = 标签.objects.all().order_by('排序', 'id')
        return Response({'ok': True, '列表': [
            {'id': 一.id, '名称': 一.名称, '系统内置': bool(一.系统内置), '排序': 一.排序}
            for 一 in 行
        ]})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
