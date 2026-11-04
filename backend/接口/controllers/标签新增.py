# -*- coding: utf-8 -*-
"""标签新增控制器：POST api/标签/新增。/script/new 手动添加题材标签，写进 题材标签 表。"""
import traceback

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.标签 import 标签
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 标签新增(请求):
    """新增标签：名称查重（已存在直接返回已有行，幂等）；所有新项目共用这一份标签库。"""
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        名称 = (请求.data.get('名称') or '').strip()
        if not 名称:
            return Response({'ok': False, 'error': '标签名不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        if len(名称) > 20:
            return Response({'ok': False, 'error': '标签名不能超过 20 字。'}, status=status.HTTP_400_BAD_REQUEST)

        已有 = 标签.objects.filter(名称=名称).first()
        if 已有 is not None:
            return Response({'ok': True, 'id': 已有.id, '名称': 已有.名称,
                             '系统内置': bool(已有.系统内置), '已存在': True})

        现在 = timezone.now()
        一行 = 标签.objects.create(
            名称=名称, 系统内置=False, 排序=0, 用户id=请求.user.id, 创建时间=现在,
        )
        return Response({'ok': True, 'id': 一行.id, '名称': 一行.名称,
                         '系统内置': False, '已存在': False})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
