# -*- coding: utf-8 -*-
"""技能上传控制器：POST 技能/上传（zip 压缩包，解压到 backend/资源/技能/目录名/）。
技能修改控制器：POST 技能/修改（改技能的分类），与上传同文件。"""
import traceback
import zipfile

from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.技能 import 技能
from 接口.models.技能分类 import 技能分类
from 接口.返回.错误 import 取错误位置


@api_view(['POST'])
def 技能上传(请求):
    """上传技能 zip：解压到 技能目录/目录名/，登记到 技能 表。"""
    try:
        文件 = 请求.FILES.get('文件')
        if 文件 is None:
            return Response(
                {'ok': False, 'error': '没有收到文件（字段名必须是 文件）。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        分类id = 请求.data.get('分类id')
        if not 分类id:
            return Response(
                {'ok': False, 'error': '缺少分类 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        原名 = 文件.name or ''
        if not 原名.lower().endswith('.zip'):
            return Response(
                {'ok': False, 'error': '技能包必须是 zip 压缩包。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        目录名 = 原名[:-4].strip()
        if not 目录名:
            return Response(
                {'ok': False, 'error': '压缩包名不能为空。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if 技能.objects.filter(目录名=目录名).exists():
            return Response(
                {'ok': False, 'error': '同名技能已存在：' + 目录名},
                status=status.HTTP_400_BAD_REQUEST,
            )

        技能目录 = settings.SKILL_DIR / 目录名
        if 技能目录.exists():
            return Response(
                {'ok': False, 'error': '技能目录已存在：' + str(技能目录)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        技能目录.mkdir(parents=True)

        try:
            with zipfile.ZipFile(文件) as 压缩包:
                for 成员 in 压缩包.namelist():
                    # 防路径穿越：跳过绝对路径和 .. 的成员
                    if 成员.startswith('/') or '..' in 成员.replace('\\', '/').split('/'):
                        continue
                    压缩包.extract(成员, 技能目录)
        except zipfile.BadZipFile:
            return Response(
                {'ok': False, 'error': '不是有效的 zip 文件。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 单根目录自动上提：zip 里若只有一层同名文件夹且根下没有 SKILL.md，
        # 把这层文件夹的内容上提到技能目录（技能包常带顶层目录，不上提会嵌套两层）
        try:
            根项 = list(技能目录.iterdir())
            if (not (技能目录 / 'SKILL.md').exists() and len(根项) == 1 and 根项[0].is_dir()):
                内层 = 根项[0]
                for 子项 in 内层.iterdir():
                    子项.rename(技能目录 / 子项.name)
                内层.rmdir()
        except OSError:
            traceback.print_exc()

        实例 = 技能.objects.create(
            目录名=目录名,
            名称=目录名,
            简介='',
            分类id_id=int(分类id),
            来源='上传压缩包',
            原压缩包名=原名,
            创建时间=timezone.now(),
            更新时间=timezone.now(),
        )
        return Response({'ok': True, 'id': 实例.id, '目录名': 目录名})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
def 技能修改(请求):
    """改一条技能的分类：只改 分类id，不动目录名/磁盘目录。"""
    try:
        技能id = 请求.data.get('id')
        if not 技能id:
            return Response(
                {'ok': False, 'error': '缺少技能 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        分类id = 请求.data.get('分类id')
        if not 分类id:
            return Response(
                {'ok': False, 'error': '缺少分类 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            实例 = 技能.objects.get(id=int(技能id))
        except 技能.DoesNotExist:
            return Response(
                {'ok': False, 'error': '技能不存在：' + str(技能id)},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            分类实例 = 技能分类.objects.get(id=int(分类id))
        except 技能分类.DoesNotExist:
            return Response(
                {'ok': False, 'error': '分类不存在：' + str(分类id)},
                status=status.HTTP_404_NOT_FOUND,
            )

        实例.分类id = 分类实例
        实例.更新时间 = timezone.now()
        实例.save(update_fields=['分类id', '更新时间'])
        return Response({'ok': True, 'id': 实例.id, '分类id': 实例.分类id_id, '分类名称': 分类实例.名称})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
