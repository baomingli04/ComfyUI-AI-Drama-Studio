# -*- coding: utf-8 -*-
"""技能分类新增控制器：POST 技能分类/新增。
技能分类删除控制器：POST 技能分类/删除（与新增同文件）。"""
import traceback

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.技能 import 技能
from 接口.models.技能分类 import 技能分类
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 技能分类新增(请求):
    """用户新增技能分类：名称必填，编码自动生成（pinyin 留空则用自增前缀）。"""
    try:
        名称 = (请求.data.get('名称') or '').strip()
        if not 名称:
            return Response(
                {'ok': False, 'error': '分类名称不能为空。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if 技能分类.objects.filter(名称=名称).exists():
            return Response(
                {'ok': False, 'error': '该分类名称已存在。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 编码唯一：用 flk_自增id 形式兜底（先占位再回填，保证 unique）
        最大id = 技能分类.objects.order_by('-id').values_list('id', flat=True).first() or 0
        编码 = 'cat_{}'.format(最大id + 1)
        while 技能分类.objects.filter(编码=编码).exists():
            最大id += 1
            编码 = 'cat_{}'.format(最大id + 1)

        实例 = 技能分类.objects.create(
            名称=名称,
            编码=编码,
            排序=0,
            系统内置=False,
            创建时间=timezone.now(),
        )
        return Response({'ok': True, 'id': 实例.id, '编码': 实例.编码})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
def 技能分类删除(请求):
    """删除技能分类：内置分类禁止删；分类下还挂着技能时禁止删。"""
    try:
        分类id = 请求.data.get('id')
        if not 分类id:
            return Response(
                {'ok': False, 'error': '缺少分类 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            实例 = 技能分类.objects.get(id=int(分类id))
        except 技能分类.DoesNotExist:
            return Response(
                {'ok': False, 'error': '分类不存在：' + str(分类id)},
                status=status.HTTP_404_NOT_FOUND,
            )

        if 实例.系统内置:
            return Response(
                {'ok': False, 'error': '内置分类不能删除：' + 实例.名称},
                status=status.HTTP_400_BAD_REQUEST,
            )

        技能数 = 技能.objects.filter(分类id_id=实例.id).count()
        if 技能数:
            return Response(
                {'ok': False, 'error': '该分类下还有 %d 个技能，先把技能移走再删。' % 技能数},
                status=status.HTTP_400_BAD_REQUEST,
            )

        实例.delete()
        return Response({'ok': True, 'id': int(分类id)})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
