# -*- coding: utf-8 -*-
"""当前用户控制器：GET 当前用户。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 当前用户(请求):
    """当前用户：带有效 token 访问，返回登录用户信息。"""
    try:
        实例 = 请求.user
        if 实例 is None:
            raise NotAuthenticated('登录状态无效，请重新登录。')

        return Response({
            'ok': True,
            'id': 实例.id,
            '用户名': 实例.用户名,
            '昵称': 实例.昵称,
        })

    except NotAuthenticated:
        raise

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=500,
        )
