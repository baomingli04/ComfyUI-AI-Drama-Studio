# -*- coding: utf-8 -*-
"""统一异常处理：任何异常都返回 {ok:false, error, file, line, func}。"""
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf异常处理

from 接口.返回.错误 import 取错误位置


def 统一异常处理(异常, 上下文):
    """DRF 全局异常处理：统一结构，并带上真实文件/行号/函数。"""
    位置 = 取错误位置(异常)

    # 已认证但无权限
    if isinstance(异常, PermissionDenied):
        return Response(
            {'ok': False, 'error': '无权限执行该操作。', 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_403_FORBIDDEN,
        )

    # 未登录 / token 无效
    if isinstance(异常, NotAuthenticated) or 异常.__class__.__name__ in ('InvalidToken', 'AuthenticationFailed'):
        return Response(
            {'ok': False, 'error': '登录状态无效，请重新登录。', 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # 资源不存在
    if isinstance(异常, Http404):
        return Response(
            {'ok': False, 'error': '请求的对象不存在。', 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 其余 DRF 异常（参数校验等）
    if isinstance(异常, APIException):
        响应 = drf异常处理(异常, 上下文)
        if 响应 is not None:
            内容 = 响应.data
            文本 = 内容 if isinstance(内容, str) else str(内容)
            响应.data = {'ok': False, 'error': 文本, 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']}
            return 响应

    # 未捕获异常：交给 DRF 处理后再套统一结构
    响应 = drf异常处理(异常, 上下文)
    if 响应 is not None:
        响应.data = {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']}
        return 响应

    return Response(
        {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
