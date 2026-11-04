# -*- coding: utf-8 -*-
"""模型配置保存控制器：POST 模型配置/保存。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.模型配置 import 模型配置
from 接口.返回.错误 import 取错误位置

可存字段 = ['大模型名称', 'LLM地址', 'LLM密钥', 'LLM模型名', 'ComfyUI地址', 'ComfyUI工作流目录', 'ComfyUI输出目录']


@api_view(['POST'])
def 模型配置保存(请求):
    """保存模型配置（单行，没有则建行）。"""
    try:
        实例 = 模型配置.objects.first()
        if 实例 is None:
            from django.utils import timezone
            实例 = 模型配置.objects.create(更新时间=timezone.now())

        for 字段 in 可存字段:
            if 字段 in 请求.data:
                setattr(实例, 字段, (请求.data.get(字段) or '').strip())

        from django.utils import timezone
        实例.更新时间 = timezone.now()
        实例.save()

        return Response({'ok': True, 'id': 实例.id})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
