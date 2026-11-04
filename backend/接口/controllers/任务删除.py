# -*- coding: utf-8 -*-
"""任务删除控制器：POST 任务/删除。

只允许删终态任务（成功 / 失败 / 中断 / 已取消）；过程态还在跑，直接拒绝，
免得执行线程还在往这一行写。删除动作 = 删 task 这一行 + 删该行的产物文件
（产物图片 / 产物图片2 / 产物视频1 / 产物视频2，落在 backend/资源/产物/ 下）。
输入文件（上传/）属于用户素材，不删。
"""
import traceback
from pathlib import Path

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from 接口.models.task import task
from 接口.返回.错误 import 取错误位置

# 终态：只有这些状态才允许删除（见 docs/02 §3.5 状态枚举）
终态集合 = ('成功', '失败', '中断', '已取消')

# 产物列（值形如 产物/task_58_1.mp4，相对 资源/ 目录）
产物列集合 = ('产物图片', '产物图片2', '产物视频1', '产物视频2')


@api_view(['POST'])
def 任务删除(请求):
    """删除单个任务：删库行 + 连产物文件一起删。"""
    try:
        任务id = 请求.data.get('id')
        if not 任务id:
            return Response(
                {'ok': False, 'error': '缺少任务 id。'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            实例 = task.objects.get(id=int(任务id))
        except task.DoesNotExist:
            return Response(
                {'ok': False, 'error': '任务不存在：' + str(任务id)},
                status=status.HTTP_404_NOT_FOUND,
            )

        if 实例.状态 not in 终态集合:
            return Response(
                {'ok': False, 'error': '任务还在跑（%s），请先取消。' % 实例.状态},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 先删磁盘产物，再删库行；文件删失败不阻断删行（库行才是主体）
        已删文件 = []
        未删文件 = []
        资源根 = Path(settings.RESOURCE_DIR).resolve()
        产物根 = Path(settings.OUTPUT_DIR).resolve()
        for 列名 in 产物列集合:
            相对路径 = (getattr(实例, 列名) or '').strip()
            if not 相对路径:
                continue
            目标 = (资源根 / 相对路径).resolve()
            # 只删 产物/ 目录下的文件：既防路径穿越，也防误删上传素材
            if not str(目标).startswith(str(产物根)):
                未删文件.append(相对路径)
                continue
            原存在 = 目标.is_file()
            try:
                目标.unlink()
            except OSError:
                # Windows 上 unlink 偶发「文件已删掉却抛 SHFileOperationW 0x2」，
                # 不认异常，下面一律按文件实际还在不在判定
                pass
            if 目标.exists():
                未删文件.append(相对路径)
            elif 原存在:
                已删文件.append(目标.name)

        实例.delete()
        return Response({'ok': True, '已删文件': 已删文件, '未删文件': 未删文件})

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return Response(
            {'ok': False, 'error': str(异常), 'file': 位置['file'], 'line': 位置['line'], 'func': 位置['func']},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
