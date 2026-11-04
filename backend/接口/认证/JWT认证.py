# -*- coding: utf-8 -*-
"""JWT 认证：从请求头或查询参数取 token 校验，并返回平台 用户 实例。"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from 接口.models.用户 import 用户


class JWT认证(JWTAuthentication):
    """JWT 认证类：校验成功返回 用户 模型实例，失败抛认证异常。"""

    def authenticate(self, 请求):
        """优先请求头 Bearer token；没有时支持 ?token=（供浏览器直链下载用）。"""
        头 = 请求.META.get('HTTP_AUTHORIZATION', '')
        if not 头:
            查询token = 请求.query_params.get('token')
            if 查询token:
                请求.META['HTTP_AUTHORIZATION'] = 'Bearer ' + 查询token
        return super().authenticate(请求)

    def get_user(self, validated_token):
        """按 token 中的 user_id 取出用户；用户不存在或未启用则抛异常。"""
        try:
            用户id = validated_token.get('user_id')
            实例 = 用户.objects.get(id=用户id)
        except 用户.DoesNotExist:
            raise InvalidToken('用户不存在或已删除。')

        if not 实例.启用:
            raise InvalidToken('用户已被停用。')

        return 实例
