# -*- coding: utf-8 -*-
"""技能删除控制器：POST 技能/删除。删记录连目录一起删。"""
import shutil
import traceback

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.技能 import 技能
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 技能删除(请求):
    """删除技能：删数据库记录 + 连技能目录一起删。"""
    try:
        技能id = 请求.data.get('id')
        if not 技能id:
            return Response(
                {'ok': False, 'error': '缺少技能 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            实例 = 技能.objects.get(id=int(技能id))
        except 技能.DoesNotExist:
            return Response(
                {'ok': False, 'error': '技能不存在：' + str(技能id)},
                status=status.HTTP_404_NOT_FOUND,
            )

        技能目录 = settings.SKILL_DIR / 实例.目录名
        if 技能目录.exists():
            shutil.rmtree(技能目录)

        实例.delete()
        return Response({'ok': True})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
