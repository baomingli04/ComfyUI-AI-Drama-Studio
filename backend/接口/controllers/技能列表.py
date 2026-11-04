# -*- coding: utf-8 -*-
"""技能列表控制器：GET 技能。"""
import traceback

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.技能 import 技能
from 接口.返回.错误 import 取错误位置


@api_view(['GET'])
def 技能列表(请求):
    """技能全量列表，可带 ?分类id= 过滤。"""
    try:
        行 = 技能.objects.select_related('分类id').order_by('-id')
        分类id = 请求.query_params.get('分类id')
        if 分类id:
            行 = 行.filter(分类id_id=int(分类id))

        列表 = [
            {
                'id': 一行.id,
                '目录名': 一行.目录名,
                '名称': 一行.名称,
                '简介': 一行.简介 or '',
                '分类id': 一行.分类id_id,
                '分类名称': 一行.分类id.名称,
                '来源': 一行.来源,
                '原压缩包名': 一行.原压缩包名 or '',
                '创建时间': 一行.创建时间.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for 一行 in 行
        ]
        return Response({'ok': True, '列表': 列表})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
