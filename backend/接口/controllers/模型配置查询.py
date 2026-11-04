# -*- coding: utf-8 -*-
"""模型配置查询控制器：GET 模型配置。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.模型配置 import 模型配置
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 模型配置查询(请求):
    """取模型配置（单行，没有则建空行）。"""
    try:
        实例 = 模型配置.objects.first()
        if 实例 is None:
            from django.utils import timezone
            实例 = 模型配置.objects.create(更新时间=timezone.now())

        return Response({
            'ok': True,
            'id': 实例.id,
            '大模型名称': 实例.大模型名称 or '',
            'LLM地址': 实例.LLM地址 or '',
            'LLM密钥': 实例.LLM密钥 or '',
            'LLM模型名': 实例.LLM模型名 or '',
            'ComfyUI地址': 实例.ComfyUI地址 or '',
            'ComfyUI工作流目录': 实例.ComfyUI工作流目录 or '',
            'ComfyUI输出目录': 实例.ComfyUI输出目录 or '',
        })

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
