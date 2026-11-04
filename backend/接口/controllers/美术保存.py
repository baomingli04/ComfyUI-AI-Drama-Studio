# -*- coding: utf-8 -*-
"""美术保存控制器：POST api/美术/保存 {id, 字段们}。单行 PATCH 美术定装。

白名单字段：生图提示词/必须保持/禁止出现/全局风格/画幅/分辨率/生图状态/
音色提示词/音色名/音色url/音色状态/音色模型/音色积分。
归属校验：定装 → 资产 → 剧 的用户id 必须等于当前登录用户。
"""
import traceback
import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.剧 import 剧
from 接口.models.资产 import 资产
from 接口.models.美术定装 import 美术定装
from 接口.返回.错误 import 取错误位置

定装字段 = {
    '全局风格': 100, '画幅': 20, '分辨率': 20,
    '生图提示词': None, '必须保持': None, '禁止出现': None, '生图状态': 10,
    '音色提示词': None, '音色url': 512, '音色状态': 10, '音色模型': 100, '音色名': 100,
}


@api_view(['POST'])
def 美术保存(请求):
    try:
        if 请求.user is None or not getattr(请求.user, 'id', None):
            return Response({'ok': False, 'error': '登录状态无效，请重新登录。'},
                            status=status.HTTP_401_UNAUTHORIZED)

        数据 = 请求.data if isinstance(请求.data, dict) else {}
        try:
            定装id = int(数据.get('id'))
        except (TypeError, ValueError):
            return Response({'ok': False, 'error': '缺少定装 id。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            定装 = 美术定装.objects.get(id=定装id)
        except 美术定装.DoesNotExist:
            return Response({'ok': False, 'error': '定装行不存在。'}, status=status.HTTP_404_NOT_FOUND)

        资产行 = 资产.objects.filter(id=定装.资产行id).first()
        剧行 = 剧.objects.filter(id=资产行.剧id).first() if 资产行 else None
        if not 剧行 or 剧行.用户id != 请求.user.id:
            return Response({'ok': False, 'error': '剧不存在或无权操作。'}, status=status.HTTP_404_NOT_FOUND)

        改动 = 0
        必填默认 = ('画幅', '分辨率', '生图状态', '音色状态')
        for 键, 长度 in 定装字段.items():
            if 键 not in 数据:
                continue
            值 = str(数据.get(键) if 数据.get(键) is not None else '').strip()
            if 长度 and len(值) > 长度:
                值 = 值[:长度]
            if not 值 and 键 not in 必填默认:
                值 = ''
            setattr(定装, 键, 值)
            改动 += 1

        if '音色积分' in 数据:
            try:
                定装.音色积分 = float(数据.get('音色积分')) if 数据.get('音色积分') not in (None, '') else None
                改动 += 1
            except (TypeError, ValueError):
                pass

        定装.更新时间 = datetime.datetime.now()
        定装.save()
        return Response({'ok': True, '改动': 改动})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
