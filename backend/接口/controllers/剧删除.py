# -*- coding: utf-8 -*-
"""剧删除 / 剧修改 控制器。

- POST 剧/删除：删行（方案/剧本/分镜/成片等子表由数据库外键 CASCADE 级联删）。
- POST 剧/修改：局部更新 封面图片 / 保存地址 / 状态 / 创意（归属校验后）。
"""
import traceback

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.返回.错误 import 取错误位置


def _取本人剧(请求, 剧id):
    """取当前用户的剧；不存在或非本人返回 None。"""
    if 请求.user is None or not getattr(请求.user, 'id', None):
        return None
    try:
        return 剧.objects.get(id=剧id, 用户id=请求.user.id)
    except 剧.DoesNotExist:
        return None


@api_view(['POST'])
def 剧删除(请求):
    """删除剧：仅本人可删；子表由外键 CASCADE 级联删除，不可恢复。"""
    try:
        try:
            剧id = int(请求.data.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        一行 = _取本人剧(请求, 剧id)
        if 一行 is None:
            return Response({'ok': False, 'error': '剧不存在或无权删除。'}, status=status.HTTP_404_NOT_FOUND)

        剧名 = 一行.剧名
        一行.delete()
        return Response({'ok': True, '剧名': 剧名})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
def 剧修改(请求):
    """修改剧：只允许 封面图片/保存地址/状态/创意 四个字段；状态限枚举值。"""
    try:
        try:
            剧id = int(请求.data.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少剧 id。'}, status=status.HTTP_400_BAD_REQUEST)

        一行 = _取本人剧(请求, 剧id)
        if 一行 is None:
            return Response({'ok': False, 'error': '剧不存在或无权修改。'}, status=status.HTTP_404_NOT_FOUND)

        允许状态 = ('草稿', '创作中', '已完成')
        改了 = []
        if '封面图片' in 请求.data:
            一行.封面图片 = (请求.data.get('封面图片') or '').strip() or None
            改了.append('封面图片')
        if '保存地址' in 请求.data:
            一行.保存地址 = (请求.data.get('保存地址') or '').strip() or None
            改了.append('保存地址')
        if '创意' in 请求.data:
            新创意 = (请求.data.get('创意') or '').strip()
            if len(新创意) < 20:
                return Response({'ok': False, 'error': '创意至少写 20 个字。'}, status=status.HTTP_400_BAD_REQUEST)
            一行.创意 = 新创意
            改了.append('创意')
        if '状态' in 请求.data:
            新状态 = (请求.data.get('状态') or '').strip()
            if 新状态 not in 允许状态:
                return Response({'ok': False, 'error': '状态只能是：' + '/'.join(允许状态)},
                                status=status.HTTP_400_BAD_REQUEST)
            一行.状态 = 新状态
            改了.append('状态')

        if not 改了:
            return Response({'ok': False, 'error': '没有可更新的字段。'}, status=status.HTTP_400_BAD_REQUEST)

        一行.更新时间 = timezone.now()
        一行.save(update_fields=改了 + ['更新时间'])
        return Response({'ok': True, '改了': 改了})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
