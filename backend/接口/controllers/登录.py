# -*- coding: utf-8 -*-
"""登录控制器：POST 登录。"""
import traceback

from django.contrib.auth.hashers import check_password
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from 接口.models.用户 import 用户
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
@permission_classes([AllowAny])
def 登录(请求):
    """登录：用户名+密码，校验通过签发 JWT access token。"""
    try:
        用户名 = (请求.data.get('用户名') or '').strip()
        密码 = 请求.data.get('密码') or ''

        if not 用户名 or not 密码:
            return Response(
                {'ok': False, 'error': '用户名和密码不能为空。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            实例 = 用户.objects.get(用户名=用户名)
        except 用户.DoesNotExist:
            return Response(
                {'ok': False, 'error': '用户名或密码错误。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not 实例.启用:
            return Response(
                {'ok': False, 'error': '该用户已被停用。'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not check_password(密码, 实例.密码哈希):
            return Response(
                {'ok': False, 'error': '用户名或密码错误。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = str(AccessToken.for_user(实例))
        except TokenError as token异常:
            位置 = 取错误位置(token异常)
            return Response(
                {'ok': False, 'error': f'签发token失败：{token异常}', 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({'ok': True, 'token': token, '用户名': 实例.用户名, '昵称': 实例.昵称})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
