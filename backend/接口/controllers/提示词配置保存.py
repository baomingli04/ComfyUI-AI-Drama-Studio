# -*- coding: utf-8 -*-
"""提示词配置保存：POST api/提示词/配置/保存。

body: { 类型, 内容 }
按 类型 upsert 一行，内容原样写入 系统提示词 列（不加工、不拼接）。
"""
import traceback

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from 接口.models.提示词模板 import 提示词模板
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 提示词配置保存(请求):
    """按类型保存提示词配置（有则改，无则建）。"""
    try:
        数据 = 请求.data or {}
        类型 = (数据.get('类型') or '').strip()
        if not 类型:
            raise ValueError('类型不能为空')
        内容 = 数据.get('内容')
        内容 = '' if 内容 is None else str(内容)

        现在 = timezone.now()
        实例 = 提示词模板.objects.filter(类型=类型).first()
        if 实例 is None:
            提示词模板.objects.create(
                类型=类型, 系统提示词=内容, 创建时间=现在, 更新时间=现在)
        else:
            实例.系统提示词 = 内容
            实例.更新时间 = 现在
            实例.save(update_fields=['系统提示词', '更新时间'])

        return Response({'ok': True, '类型': 类型})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
